"""
Contains shared utilities for serializing and deserializing objects.
"""

from __future__ import annotations

import collections.abc
import enum
import functools
import inspect
import json
import types
import typing as t

import introspection.types
import uniserde
from uniserde import Jsonable, JsonDoc

import rio

from . import color, fills, inspection, maybes, session
from .components import fundamental_component
from .observables.dataclass import class_local_fields
from .self_serializing import SelfSerializing

__all__ = ["serialize_json", "serialize_and_host_component"]


T = t.TypeVar("T")


# A globally shared JSON serializer/deserializer. These are caching, so reusing
# the same one is beneficial.
json_serde = uniserde.JsonSerde.new_camel_case()


Serializer = t.Callable[["session.Session", T], Jsonable]


FILL_LIKES = {*t.get_args(fills._FillLike), None, type(None)}


def _float_or_zero(obj: object) -> float:
    try:
        return float(obj)  # type: ignore
    except (ValueError, TypeError):
        return 0


def _serialize_special_types(obj: object) -> Jsonable:
    try:
        func = maybes.TYPE_NORMALIZERS[type(obj)]
    except KeyError:
        raise TypeError(
            f"Can't serialize {obj!r} of type {type(obj)} as JSON"
        ) from None

    return func(obj)  # type: ignore


def _get_margin(*margins: float | None) -> float:
    for margin in margins:
        if margin is not None:
            return margin

    return 0


def serialize_json(data: Jsonable) -> str:
    """
    Like `json.dumps`, but can also serialize numpy types.
    """
    try:
        return json.dumps(data, default=_serialize_special_types)
    except TypeError:
        # Re-initialize the maybes, someone probably imported numpy/pandas after
        # the app was started
        maybes.initialize(force=True)
        return json.dumps(data, default=_serialize_special_types)


def serialize_and_host_component(
    component: rio.Component, changed_properties: t.Iterable[str]
) -> JsonDoc:
    """
    Serializes the component, non-recursively. Children are serialized just by
    their `_id`.

    Non-fundamental components must have been built, and their output cached in
    the session.
    """
    result: JsonDoc = {
        "_python_type_": type(component).__name__,
        "_rio_internal_": component._rio_internal_,
        "key": component.key,
        "accessibility_role": component.accessibility_role,
        # SCROLLING-REWORK "_scroll_": [component.scroll_x, component.scroll_y],
    }

    # Accessing state properties is pretty slow, so we'll store these in local
    # variables
    min_width = component.min_width
    min_height = component.min_height

    # MAX-SIZE-BRANCH max_width = component.max_width
    # MAX-SIZE-BRANCH max_height = component.max_height

    grow_x = component.grow_x
    grow_y = component.grow_y

    margin_x = component.margin_x
    margin_y = component.margin_y
    margin = component.margin

    # Add layout properties, in a more succinct way than sending them separately
    result["_margin_"] = (
        _get_margin(component.margin_left, margin_x, margin),
        _get_margin(component.margin_top, margin_y, margin),
        _get_margin(component.margin_right, margin_x, margin),
        _get_margin(component.margin_bottom, margin_y, margin),
    )
    # The width/height can be floats or strings, but they could also be numpy
    # floats or numpy strings. We could check `isinstance(width,
    # maybes.STR_TYPES)`, but that would give incorrect output if numpy was
    # imported after the app was launched. I think the easiest solution is to
    # simply try converting it to a float, and if that fails, default to 0.
    # (Although that has the side effect of treating strings like `"1.5"` as
    # numbers.)
    result["_min_size_"] = (
        _float_or_zero(min_width),
        _float_or_zero(min_height),
    )
    # MAX-SIZE-BRANCH result["_max_size_"] = (
    # MAX-SIZE-BRANCH     _float_if_not_none(max_width),
    # MAX-SIZE-BRANCH     _float_if_not_none(max_height),
    # MAX-SIZE-BRANCH )
    result["_align_"] = (
        component.align_x,
        component.align_y,
    )
    result["_grow_"] = (grow_x, grow_y)

    # If it's a fundamental component, serialize its state because JS needs it.
    # For non-fundamental components, there's no reason to send the state to
    # the frontend.
    if isinstance(component, fundamental_component.FundamentalComponent):
        sess = component.session
        serializers = get_attribute_serializers(type(component))

        for name in changed_properties:
            try:
                serializer = serializers[name]
            except KeyError:
                # This happens for properties inherited from Component, like
                # `margin` or `min_width`
                continue

            result[name] = serializer(sess, getattr(component, name))

        # Encode any internal additional state. Doing it this late allows the
        # custom serialization to overwrite automatically generated values.
        result["_type_"] = component._unique_id_
        result.update(component._custom_serialize_())

    # Dialog containers are a special case. These must be high-level on the
    # Python side, so that their children can correctly track their builder, but
    # they must be low-level on the JS side, so that they can run custom code.
    #
    # -> Pretend it's a fundamental component
    elif isinstance(component, rio.components.dialog_container.DialogContainer):
        result["_type_"] = "DialogContainer-builtin"
        result["content"] = component._build_data_.build_result._id_  # type: ignore
        result.update(component.serialize())

    else:
        # Take care to add underscores to any properties here, as the
        # user-defined state is also added and could clash
        result["_type_"] = "HighLevelComponent-builtin"
        result["_child_"] = component._build_data_.build_result._id_  # type: ignore

    return result


@functools.lru_cache(maxsize=None)
def get_attribute_serializers(
    cls: t.Type[rio.Component],
) -> t.Mapping[str, Serializer]:
    """
    Returns a dictionary of attribute names to their types that should be
    serialized for the given component class.
    """
    if cls is rio.Component:
        return {}

    serializers: dict[str, Serializer] = {}

    for base_cls in reversed(cls.__bases__):
        if issubclass(base_cls, rio.Component):
            serializers.update(get_attribute_serializers(base_cls))

    annotations = inspection.get_local_annotations(cls)

    for attr_name, field in class_local_fields(cls).items():
        if not field.serialize:
            assert attr_name not in serializers, (
                f"A base class wants to serialize {attr_name}, but {cls} doesn't"
            )
            continue

        serializer = _get_serializer_for_annotation(annotations[attr_name])
        if serializer is None:
            continue

        serializers[attr_name] = serializer

    return serializers


def _serialize_basic_json_value(
    sess: session.Session, value: Jsonable
) -> Jsonable:
    return value


def _serialize_self_serializing(
    sess: session.Session, obj: SelfSerializing
) -> Jsonable:
    return obj._serialize(sess)


def _serialize_child_component(
    sess: session.Session, component: rio.Component
) -> Jsonable:
    return component._id_


def _serialize_sequence(
    sess: session.Session,
    sequence: t.Sequence[T],
    item_serializer: Serializer[T],
) -> Jsonable:
    return [item_serializer(sess, item) for item in sequence]


def _serialize_enum(
    sess: session.Session, value: object, as_type: t.Type[enum.Enum]
) -> Jsonable:
    return json_serde.as_json(value, as_type=as_type)


def _serialize_colorset(
    sess: session.Session, colorset: color.ColorSet
) -> Jsonable:
    return sess.theme._serialize_colorset(colorset)


def _serialize_fill_like(
    sess: session.Session, fill: fills._FillLike | None
) -> Jsonable:
    return sess._serialize_fill(fill)


def _serialize_optional(
    sess: session.Session, value: T | None, serializer: Serializer[T]
) -> Jsonable:
    if value is None:
        return None

    return serializer(sess, value)


def _get_serializer_for_annotation(
    annotation: introspection.types.TypeAnnotation,
) -> Serializer | None:
    """
    Which values are serialized for state depends on the annotated datatypes.
    There is no point in sending fancy values over to the client which it can't
    interpret.

    This function looks at the annotation and returns a suitable serialization
    function, or `None` if this attribute shouldn't be serialized.
    """
    # Basic JSON values
    if annotation in (int, float, str, bool, None):
        return _serialize_basic_json_value

    origin = t.get_origin(annotation)
    args = t.get_args(annotation)

    # Python 3.10 crashes if you try `issubclass(list[str], SelfSerializing)`,
    # so we must make absolutely sure the annotation isn't a generic type
    if inspect.isclass(annotation) and not args:
        # Self-Serializing
        if issubclass(annotation, SelfSerializing):
            return _serialize_self_serializing

        # Components
        if issubclass(annotation, rio.Component):
            return _serialize_child_component

        # Enums
        if issubclass(annotation, enum.Enum):
            return functools.partial(_serialize_enum, as_type=annotation)

    # Sequences of serializable values
    if origin in (list, t.Sequence, collections.abc.Sequence):
        item_serializer = _get_serializer_for_annotation(args[0])
        if item_serializer is None:
            return None

        return functools.partial(
            _serialize_sequence, item_serializer=item_serializer
        )

    # Literal
    if origin is t.Literal:
        return _serialize_basic_json_value

    if origin in (t.Union, types.UnionType):
        # ColorSet
        if set(args) == color._color_set_args:
            return _serialize_colorset

        # Optional
        if len(args) == 2 and type(None) in args:
            type_ = next(type_ for type_ in args if type_ is not type(None))
            serializer = _get_serializer_for_annotation(type_)
            if serializer is None:
                return None
            return functools.partial(_serialize_optional, serializer=serializer)

        # Fills
        #
        # Note: FILL_LIKES includes `None` and `Color`. We don't want a `None |
        # Color` to be serialized as a Fill, so this code must be below the
        # `Optional` check.
        if set(args) <= FILL_LIKES:
            return _serialize_fill_like

        # Multiple kinds of components
        if all(
            isinstance(arg, type) and issubclass(arg, rio.Component)
            for arg in args
        ):
            return _serialize_child_component

    return None
