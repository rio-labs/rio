from __future__ import annotations

import collections.abc
import functools
import inspect
import sys
import types
import typing as t

import introspection.typing

import rio

__all__ = [
    "get_local_annotations",
    "get_resolved_type_annotations",
    "get_child_component_containing_attribute_names",
    "get_child_component_containing_attribute_names_for_builtin_components",
]


_EXPLICITLY_SET_STATE_PROPERTY_NAMES_CACHE: dict[
    tuple[t.Type[rio.Component], int, frozenset[str]], frozenset[str]
] = {}


# Note: This function purposely isn't cached because calling it at different
# times can give different outputs. For example, if called immediately after the
# input class has been created, some forward references may not be evaluatable
# yet.
class get_local_annotations(t.Mapping[str, introspection.types.TypeAnnotation]):
    def __init__(self, cls: type, *, strict: bool = False) -> None:
        # Note: Don't use `typing.get_type_hints` because it has a stupid bug in
        # python 3.10 where it dies if something is annotated as
        # `dataclasses.KW_ONLY`.
        self._annotations: dict = vars(cls).get("__annotations__", {})
        self._module = sys.modules[cls.__module__]
        self._strict = strict

    def __getitem__(self, name: str) -> introspection.types.TypeAnnotation:
        return introspection.typing.resolve_forward_refs(
            self._annotations[name],
            self._module,
            mode="ast",
            strict=self._strict,
            treat_name_errors_as_imports=True,
        )

    def __iter__(self) -> t.Iterator[str]:
        return iter(self._annotations)

    def __len__(self) -> int:
        return len(self._annotations)


def get_resolved_type_annotations(
    cls: type,
) -> t.Mapping[str, type]:
    maps = [get_local_annotations(c, strict=True) for c in cls.__mro__]
    return collections.ChainMap(*maps)  # type: ignore


@functools.lru_cache(maxsize=None)
def get_child_component_containing_attribute_names(
    cls: type,
) -> t.Collection[str]:
    attr_names = set[str]()

    for base_cls in cls.__bases__:
        attr_names.update(
            get_child_component_containing_attribute_names(base_cls)
        )

    for attr_name, annotation in get_local_annotations(cls).items():
        if annotation_contains_component(annotation):
            attr_names.add(attr_name)

    return tuple(attr_names)


def annotation_contains_component(
    annotation: introspection.types.TypeAnnotation,
) -> bool:
    # In python 3.10, there's no easy way to check if an annotation is really a
    # class. (`isinstance(set[str], type)` returns `True`, for example.) So
    # we'll just catch the error.
    try:
        if issubclass(annotation, rio.Component):  # type: ignore
            return True
    except TypeError:
        pass

    origin = t.get_origin(annotation)
    args = t.get_args(annotation)

    if not args:
        return False

    # Note: Because of the way `remap_components` is written, we only support
    # mutable sequences at the moment
    if origin in (
        list,
        t.List,
        t.MutableSequence,
        collections.abc.MutableSequence,
    ):
        return annotation_contains_component(args[0])

    if origin in (t.Union, types.UnionType):
        return any(annotation_contains_component(arg) for arg in args)

    if origin is t.Annotated:
        return annotation_contains_component(args[0])

    return False


@functools.lru_cache(maxsize=None)
def get_child_component_containing_attribute_names_for_builtin_components() -> (
    t.Mapping[str, t.Collection[str]]
):
    from .components.fundamental_component import FundamentalComponent

    result = {
        cls._unique_id_: get_child_component_containing_attribute_names(cls)
        for cls in introspection.iter_subclasses(FundamentalComponent)
        if cls._unique_id_.endswith("-builtin")
    }

    result.update(
        {
            "HighLevelComponent-builtin": ["_child_"],
        }
    )
    return result


def get_explicitly_set_state_property_names(
    component: rio.Component,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> frozenset[str]:
    """
    Given a component and the arguments passed to its constructor, return the
    names of the state properties that were explicitly provided to the
    constructor. The results are cached.

    Note that really only _state properties_ are returned. Any parameters that
    don't match state properties are discarded.
    """

    # Try to get the result from the cache
    key = (type(component), len(args), frozenset(kwargs.keys()))

    try:
        return _EXPLICITLY_SET_STATE_PROPERTY_NAMES_CACHE[key]
    except KeyError:
        pass

    # No cache entry for this exists yet so determine the result the slow way
    signature = inspect.signature(component.__init__)
    bound_args = signature.bind(*args, **kwargs)

    # Anything passed in is explicitly set
    result = set(bound_args.arguments)

    # *args and **kwargs are always explicitly set
    result.update(
        param.name
        for param in signature.parameters.values()
        if param.kind
        in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        )
    )

    # Discard parameters that don't correspond to state properties
    result.intersection_update(type(component)._observable_properties_)

    # Freeze the result so nobody gets silly ideas
    result = frozenset(result)

    # Store the result in the cache for future use
    _EXPLICITLY_SET_STATE_PROPERTY_NAMES_CACHE[key] = result

    return result
