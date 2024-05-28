import functools
import warnings
from typing import *

from .components import component as component_meta

__all__ = ["deprecated", "parameters_renamed", "_remap_kwargs"]


C = TypeVar("C", bound=Union[Callable, "component_meta.ComponentMeta"])


def deprecated(*, since: str, description: str):
    def decorator(callable_: C) -> C:
        callable_.__rio_deprecated_since = since  # type: ignore
        callable_.__rio_deprecated_description = description  # type: ignore
        return callable_

    return decorator


def parameters_renamed(old_names_to_new_names: Mapping[str, str]):
    """
    Class/Function decorator that allows it to be called with the old names of
    the given parameters. For example:

        @parameters_renamed({'foo': 'bar'})
        def example_func(bar: int):
            return bar

        example_func(foo=3)  # Ok at runtime, but static type checker complains
    """

    def decorator(callable_: C) -> C:
        if isinstance(callable_, component_meta.ComponentMeta):
            callable_._deprecated_parameter_names_.update(
                old_names_to_new_names
            )
            return callable_

        @functools.wraps(callable_)  # type: ignore (wtf?)
        def wrapper(*args, **kwargs):
            _remap_kwargs(callable_.__name__, kwargs, old_names_to_new_names)
            return callable_(*args, **kwargs)  # type: ignore (wtf?)

        return wrapper  # type: ignore (wtf?)

    return decorator


def _remap_kwargs(
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
            warnings.warn(
                f"The {old_name!r} parameter of rio.{func_name} is deprecated; it has been renamed to {new_name!r}",
                RioDeprecationWarning,
            )


class RioDeprecationWarning(Warning):
    pass
