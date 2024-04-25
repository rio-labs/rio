from __future__ import annotations

import collections
import functools
import sys
from collections.abc import Collection, Iterator, Mapping

import introspection.typing

import rio

__all__ = [
    "get_local_annotations",
    "get_resolved_type_annotations",
    "get_child_component_containing_attribute_names",
    "get_child_component_containing_attribute_names_for_builtin_components",
]


# Note: This function purposely isn't cached because calling it at different
# times can give different outputs. For example, if called immediately after the
# input class has been created, some forward references may not be evaluatable
# yet.
class get_local_annotations(Mapping[str, introspection.types.TypeAnnotation]):
    def __init__(self, cls: type, *, strict: bool = False):
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

    def __iter__(self) -> Iterator[str]:
        return iter(self._annotations)

    def __len__(self) -> int:
        return len(self._annotations)


def get_resolved_type_annotations(
    cls: type,
) -> Mapping[str, type]:
    maps = [get_local_annotations(c, strict=True) for c in cls.__mro__]
    return collections.ChainMap(*maps)  # type: ignore


@functools.lru_cache(maxsize=None)
def get_child_component_containing_attribute_names(
    cls: type[rio.Component],
) -> Collection[str]:
    from . import serialization

    attr_names: list[str] = []

    for attr_name, serializer in serialization.get_attribute_serializers(
        cls
    ).items():
        # : Component
        if serializer is serialization._serialize_child_component:
            attr_names.append(attr_name)
        elif isinstance(serializer, functools.partial):
            # : Component | None
            if (
                serializer.func is serialization._serialize_optional
                and serializer.keywords["serializer"]
                is serialization._serialize_child_component
            ):
                attr_names.append(attr_name)
            # : list[Component]
            elif (
                serializer.func is serialization._serialize_list
                and serializer.keywords["item_serializer"]
                is serialization._serialize_child_component
            ):
                attr_names.append(attr_name)

    return tuple(attr_names)


@functools.lru_cache(maxsize=None)
def get_child_component_containing_attribute_names_for_builtin_components() -> (
    Mapping[str, Collection[str]]
):
    from .components.fundamental_component import FundamentalComponent

    result = {
        cls._unique_id: get_child_component_containing_attribute_names(cls)
        for cls in introspection.iter_subclasses(FundamentalComponent)
        if cls._unique_id.endswith("-builtin")
    }

    result.update(
        {
            "Placeholder": ["_child_"],
            "Align-builtin": ["child"],
            "Margin-builtin": ["child"],
        }
    )
    return result
