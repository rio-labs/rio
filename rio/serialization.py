from __future__ import annotations

import enum
import functools
import inspect
import json
import types
from typing import *  # type: ignore

import introspection.types
import uniserde
from uniserde import Jsonable, JsonDoc

import rio

from . import color, inspection, maybes, session
from .components import fundamental_component
from .dataclass import class_local_fields
from .self_serializing import SelfSerializing

__all__ = ["serialize_json", "serialize_and_host_component"]


T = TypeVar("T")
Serializer = Callable[["session.Session", T], Jsonable]


def _float_or_zero(obj: object) -> float:
    try:
        return float(obj)  # type: ignore
    except ValueError:
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


def serialize_and_host_component(component: rio.Component) -> JsonDoc:
    """
    Serializes the component, non-recursively. Children are serialized just by
    their `_id`.

    Non-fundamental components must have been built, and their output cached in
    the session.
    """
    result: JsonDoc = {
        "_python_type_": type(component).__name__,
        "_key_": component.key,
        "_rio_internal_": component._rio_internal_,
    }

    # Accessing state properties is pretty slow, so we'll store these in local
    # variables
    width = component.width
    height = component.height

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
    result["_size_"] = (_float_or_zero(width), _float_or_zero(height))
    result["_align_"] = (
        component.align_x,
        component.align_y,
    )
    result["_grow_"] = (
        width == "grow",
        height == "grow",
    )

    # If it's a fundamental component, serialize its state because JS needs it.
    # For non-fundamental components, there's no reason to send the state to
    # the frontend.
    if isinstance(component, fundamental_component.FundamentalComponent):
        sess = component.session

        for name, serializer in get_attribute_serializers(
            type(component)
        ).items():
            result[name] = serializer(sess, getattr(component, name))

        # Encode any internal additional state. Doing it this late allows the custom
        # serialization to overwrite automatically generated values.
        result["_type_"] = component._unique_id
        result.update(component._custom_serialize())

    else:
        # Take care to add underscores to any properties here, as the
        # user-defined state is also added and could clash
        result["_type_"] = "Placeholder"
        result["_child_"] = component.session._weak_component_data_by_component[
            component
        ].build_result._id

    return result


@functools.lru_cache(maxsize=None)
def get_attribute_serializers(
    cls: Type[rio.Component],
) -> Mapping[str, Serializer]:
    """
    Returns a dictionary of attribute names to their types that should be
    serialized for the given component class.
    """
    serializers: dict[str, Serializer] = {}

    for base_cls in reversed(cls.__bases__):
        if issubclass(base_cls, rio.Component):
            serializers.update(get_attribute_serializers(base_cls))

    annotations = inspection.get_local_annotations(cls)

    for attr_name, field in class_local_fields(cls).items():
        if not field.serialize:
            assert (
                attr_name not in serializers
            ), f"A base class wants to serialize {attr_name}, but {cls} doesn't"
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
    return component._id


def _serialize_list(
    sess: session.Session, list_: list[T], item_serializer: Serializer[T]
) -> Jsonable:
    return [item_serializer(sess, item) for item in list_]


def _serialize_enum(
    sess: session.Session, value: object, as_type: Type[enum.Enum]
) -> Jsonable:
    return uniserde.as_json(value, as_type=as_type)


def _serialize_colorset(
    sess: session.Session, colorset: color.ColorSet
) -> Jsonable:
    return sess.theme._serialize_colorset(colorset)


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

    origin = get_origin(annotation)
    args = get_args(annotation)

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
    if origin is list:
        item_serializer = _get_serializer_for_annotation(args[0])
        if item_serializer is None:
            return None
        return functools.partial(
            _serialize_list, item_serializer=item_serializer
        )

    # Literal
    if origin is Literal:
        return _serialize_basic_json_value

    if origin in (Union, types.UnionType):
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

    return None
