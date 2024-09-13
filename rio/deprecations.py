import functools
import warnings
from typing import *  # type: ignore

from .component_meta import ComponentMeta
from .warnings import *

# The alias here is necessary to avoid ruff stupidly replacing the import with
# a `pass`.
if TYPE_CHECKING:
    import rio as rio

__all__ = [
    "deprecated",
    "_remap_kwargs",
    "component_kwarg_renamed",
    "warn",
]


CO = TypeVar("CO", bound="rio.Component")
C = TypeVar("C", bound=Union[Callable, ComponentMeta])
F = TypeVar("F", bound=Callable)


def warn(
    *,
    since: str,
    message: str,
    stacklevel: int = 1,
) -> None:
    warnings.warn(
        f"Deprecated since version {since}: {message}",
        RioDeprecationWarning,
        stacklevel=stacklevel,
    )


@overload
def deprecated(*, since: str, replacement: Callable | str): ...


@overload
def deprecated(*, since: str, description: str): ...


def deprecated(
    *,
    since: str,
    description: str | None = None,
    replacement: Callable | str | None = None,
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

    def decorator(component_class: Type[CO]) -> Type[CO]:
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
                warn(
                    since=since,
                    message=f"The `{old_name}` parameter of `rio.{component_class.__name__}` is deprecated. Please use `{new_name}` instead.",
                    stacklevel=6,
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
    **params: Callable[[Any], dict[str, Any]],
):
    """
    This is a function decorator that's quite similar to `parameters_renamed`,
    but it allows you to change the type and value(s) of the parameter as well
    as the name.

    The input for the decorator are functions that take the value of the old
    parameter as input and return a dict `{'new_parameter_name': value}`.

    Example: `Theme.from_colors` used to have a `light: bool = True` parameter
    which was changed to `mode: Literal['light', 'dark'] = 'light'`.

        class Theme:
            @parameters_remapped(
                '0.9',
                light=lambda light: {"mode": "light" if light else "dark"},
            )
            def from_colors(..., mode: Literal['light', 'dark'] = 'light'):
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

                    warn(
                        since=since,
                        message=f"The {old_name!r} parameter of rio.{func.__qualname__}"
                        f" is deprecated; please use the {new_name!r} parameter"
                        f" from now on",
                    )

            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def _remap_kwargs(
    since: str,
    func_name: str,
    kwargs: dict[str, object],
    old_names_to_new_names: Mapping[str, str],
) -> None:
    for old_name, new_name in old_names_to_new_names.items():
        try:
            kwargs[new_name] = kwargs.pop(old_name)
        except KeyError:
            pass
        else:
            warn(
                since=since,
                message=f"The {old_name!r} parameter of rio.{func_name} is deprecated. Please use `{new_name!r}` instead.",
            )
