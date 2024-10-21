import functools
import typing as t
import warnings

import introspection

from .component_meta import ComponentMeta
from .warnings import *

# The alias here is necessary to avoid ruff stupidly replacing the import with
# a `pass`.
if t.TYPE_CHECKING:
    import rio

__all__ = [
    "deprecated",
    "_remap_kwargs",
    "function_kwarg_renamed",
    "warn",
]


CO = t.TypeVar("CO", bound="rio.Component")
C = t.TypeVar("C", bound=t.Union[t.Callable, ComponentMeta])
F = t.TypeVar("F", bound=t.Callable)


def warn(
    *,
    since: str,
    message: str,
) -> None:
    # Find the first stack frame outside of Rio. Passing the stack level
    # manually is error prone because decorators like `@component_kwarg_renamed`
    # increase the call depth
    with introspection.CallStack.current() as call_stack:
        for stacklevel, frame in enumerate(reversed(call_stack), 1):
            if frame.globals["__name__"].partition(".")[0] not in (
                "rio",
                "introspection",
                "fastapi",
                "starlette",
                "uvicorn",
                "asyncio",
                "threading",
            ):
                break
        else:
            stacklevel = 0

    warnings.warn(
        f"Deprecated since Rio version {since}: {message}",
        RioDeprecationWarning,
        stacklevel=stacklevel,
    )


def warn_parameter_renamed(
    *,
    since: str,
    old_name: str,
    new_name: str,
    owner: str,
):
    warn(
        since=since,
        message=f"The `{old_name}` parameter of `{owner}` has been renamed. Use `{new_name}` instead.",
    )


@t.overload
def deprecated(*, since: str, replacement: t.Callable | str): ...


@t.overload
def deprecated(*, since: str, description: str): ...


def deprecated(
    *,
    since: str,
    description: str | None = None,
    replacement: t.Callable | str | None = None,
):
    if replacement is not None:
        if not isinstance(replacement, str):
            replacement = replacement.__qualname__

        description = f"Use {replacement} instead."

    def decorator(callable_: C) -> C:
        callable_.__rio_deprecated_since = since  # type: ignore
        callable_.__rio_deprecated_description = description  # type: ignore
        return callable_

    return decorator


def component_kwarg_renamed(
    since: str,
    old_name: str,
    new_name: str,
):
    """
    This decorator helps with renaming a parameter of a Rio component. If the
    component is passed a kwarg with the old name, it is remapped to the new
    name instead.

    Please note that this only works in very limited circumstances:

    - The parameter behavior must be the same (or the new one is more powerful)
    - The parameter must be a keyword argument (because positional arguments
      would require a very slow `inspect.signature` call)
    - This must be applied to a component, not a function (because it modifies
      the contained `_remap_constructor_arguments` method)
    """

    def decorator(component_class: t.Type[CO]) -> t.Type[CO]:
        old_remap = component_class._remap_constructor_arguments_

        @staticmethod
        @functools.wraps(old_remap)
        def new_remap(args: tuple, kwargs: dict):
            # Remap the old parameter to the new one
            try:
                kwargs[new_name] = kwargs.pop(old_name)
            except KeyError:
                pass
            else:
                warn_parameter_renamed(
                    since=since,
                    old_name=old_name,
                    new_name=new_name,
                    owner=f"rio.{component_class.__name__}",
                )

            # Delegate to the original _remap_constructor_arguments method
            return old_remap(args, kwargs)

        # Replace the original _remap_constructor_arguments method with the new one
        component_class._remap_constructor_arguments_ = new_remap

        # Return the modified class
        return component_class

    return decorator


def parameters_remapped(
    *,
    since: str,
    **params: t.Callable[[t.Any], dict[str, t.Any]],
):
    """
    This is a function decorator that's quite similar to `parameters_renamed`,
    but it allows you to change the type and value(s) of the parameter as well
    as the name.

    The input for the decorator are functions that take the value of the old
    parameter as input and return a dict `{'new_parameter_name': value}`.

    Example: `Theme.from_colors` used to have a `light: bool = True` parameter
    which was changed to `mode: t.Literal['light', 'dark'] = 'light'`.

        class Theme:
            @parameters_remapped(
                '0.9',
                light=lambda light: {"mode": "light" if light else "dark"},
            )
            def from_colors(..., mode: t.Literal['light', 'dark'] = 'light'):
                ...

        Theme.from_colors(light=False)  # Equivalent to `mode='dark'`
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for old_name, remap_func in params.items():
                try:
                    old_value = kwargs.pop(old_name)
                except KeyError:
                    pass
                else:
                    [[new_name, new_value]] = remap_func(old_value).items()
                    kwargs[new_name] = new_value

                    warn_parameter_renamed(
                        since=since,
                        old_name=old_name,
                        new_name=new_name,
                        owner=f"rio.{func.__qualname__}",
                    )

            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def _remap_kwargs(
    since: str,
    func_name: str,
    kwargs: dict[str, object],
    old_names_to_new_names: t.Mapping[str, str],
) -> None:
    for old_name, new_name in old_names_to_new_names.items():
        try:
            kwargs[new_name] = kwargs.pop(old_name)
        except KeyError:
            pass
        else:
            warn_parameter_renamed(
                since=since,
                old_name=old_name,
                new_name=new_name,
                owner=f"rio.{func_name}",
            )


def function_kwarg_renamed(
    since: str,
    old_name: str,
    new_name: str,
) -> t.Callable[[F], F]:
    """
    This decorator helps with renaming a keyword argument of a function, NOT a
    component.
    """

    def decorator(old_function: F) -> F:
        @functools.wraps(old_function)
        def new_function(*args: tuple, **kwargs: dict):
            # Remap the old parameter to the new one
            try:
                kwargs[new_name] = kwargs.pop(old_name)
            except KeyError:
                pass
            else:
                warn_parameter_renamed(
                    since=since,
                    old_name=old_name,
                    new_name=new_name,
                    owner=f"rio.{old_function.__qualname__}",
                )

            # Delegate to the original function
            return old_function(*args, **kwargs)

        # Return the modified function
        return new_function  # type: ignore

    return decorator
