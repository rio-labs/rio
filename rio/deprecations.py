import functools
import typing as t
import warnings

import imy.deprecations
from imy.deprecations import (
    deprecated,
    parameter_remapped,
    parameter_renamed,
    warn,
    warn_parameter_renamed,
)

from .warnings import RioDeprecationWarning

if t.TYPE_CHECKING:
    import rio

__all__ = [
    "deprecated",
    "parameter_renamed",
    "parameter_remapped",
    "component_kwarg_renamed",
    "warn",
    "warn_parameter_renamed",
]


def get_public_name(obj: type | t.Callable) -> str:
    # Unfortunately, we can't get the *real* public name from
    # `rio.docs.get_docs_for(obj)` here because that requires all optional
    # dependencies (pandas, polars, etc.) to be installed.
    return obj.__qualname__


imy.deprecations.configure(
    module="rio",
    project_name="Rio",
    modules_skipped_in_stacktrace=(
        "rio",
        "introspection",
        "fastapi",
        "starlette",
        "uvicorn",
        "asyncio",
        "threading",
    ),
    warning_class=RioDeprecationWarning,
    name_for_object=get_public_name,
)

# Python filters DeprecationWarnings per default. Since rio is a framework (and
# not a library), I doubt anyone will have a problem with us forcefully turning
# our warnings back on.
warnings.simplefilter("default", RioDeprecationWarning)


CO = t.TypeVar("CO", bound="rio.Component")


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
      the contained `_remap_constructor_arguments_` method)
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
                    function=component_class,
                )

            # Delegate to the original _remap_constructor_arguments method
            return old_remap(args, kwargs)

        # Replace the original _remap_constructor_arguments method with the new one
        component_class._remap_constructor_arguments_ = new_remap

        # Return the modified class
        return component_class

    return decorator
