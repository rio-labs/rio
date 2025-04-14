from __future__ import annotations

import abc
import copy
import dataclasses
import functools
import inspect
import sys
import types
import typing as t
import weakref

import imy.docstrings
import introspection
import typing_extensions as te

import rio

from .. import global_state, inspection
from .observable_property import ObservableProperty

__all__ = ["Dataclass"]


T = t.TypeVar("T")


_FIELDS_BY_CLASS: dict[type, dict[str, RioField]] = {}


def class_local_fields(cls: type) -> t.Mapping[str, RioField]:
    return _FIELDS_BY_CLASS.get(cls, {})


@functools.cache
def all_class_fields(cls: type) -> t.Mapping[str, RioField]:
    result = dict[str, RioField]()

    for cls in reversed(cls.__mro__):
        result.update(class_local_fields(cls))

    return result


@functools.cache
def all_property_names(cls: type) -> set[str]:
    result = set[str]()

    for name, field in all_class_fields(cls).items():
        if field.create_property:
            result.add(name)

    return result


class RioField(dataclasses.Field):
    __slots__ = (
        "create_property",
        "serialize",
        "annotation",
        "real_default_value",
    )

    annotation: type

    def __init__(
        self,
        *,
        init: bool = True,
        repr: bool = True,
        hash: bool = False,
        compare: bool = False,
        metadata: t.Any = None,
        kw_only: bool | dataclasses._MISSING_TYPE = dataclasses.MISSING,
        default: object = dataclasses.MISSING,
        default_factory: (
            t.Callable[[], object] | dataclasses._MISSING_TYPE
        ) = dataclasses.MISSING,
        real_default_value: object = dataclasses.MISSING,
        create_property: bool = True,
        serialize: bool = True,
    ) -> None:
        super().__init__(
            default=default,
            default_factory=default_factory,  # type: ignore
            init=init,
            repr=repr,
            hash=hash,
            compare=compare,
            metadata=metadata,
            kw_only=kw_only,  # type: ignore
        )

        self.create_property = create_property
        self.serialize = serialize
        self.real_default_value = real_default_value

    @classmethod
    def from_dataclass_field(cls, field: dataclasses.Field) -> te.Self:
        if field.default is dataclasses.MISSING:
            default = field.default
            default_factory = field.default_factory
        else:
            default = dataclasses.MISSING
            default_factory = _make_default_factory_for_value(field.default)

        return cls(
            init=field.init,
            repr=field.repr,
            default=default,
            default_factory=default_factory,
            real_default_value=field.default,
        )


def internal_field(
    *,
    default: object = dataclasses.MISSING,
    default_factory: (
        t.Callable[[], object] | dataclasses._MISSING_TYPE
    ) = dataclasses.MISSING,
    init: bool = False,
    repr: bool = False,
    create_property: bool = False,
    serialize: bool = False,
) -> t.Any:
    """
    Can be used to override settings for a Field.

    Per default, it removes the field from __init__ and __repr__ and avoids
    creating an ObservableProperty.
    """
    return RioField(
        default=default,
        default_factory=default_factory,
        create_property=create_property,
        serialize=serialize,
        init=init,
        repr=repr,
    )


def _make_default_factory_for_value(value: T) -> t.Callable[[], T]:
    return functools.partial(copy.deepcopy, value)


class DataclassProperty(ObservableProperty["Dataclass"]):
    """
    Unlike Components, which are tied to a specific Session, dataclass instances
    can be freely accessed from anywhere. That's why these Properties track all
    Sessions they were accessed from.
    """

    def __init__(
        self,
        name: str,
        raw_annotation: introspection.types.TypeAnnotation,
        module: types.ModuleType,
        readonly: bool,
    ):
        super().__init__(name, raw_annotation, module, readonly)

        self._affected_sessions: t.MutableSet[rio.Session] = weakref.WeakSet()

    def _get_affected_sessions(
        self, instance: Dataclass
    ) -> t.Iterable[rio.Session]:
        return self._affected_sessions

    def __get__(self, instance: Dataclass | None, owner: type | None = None):
        if (
            global_state.currently_building_session is not None
            and instance is not None
        ):
            self._affected_sessions.add(global_state.currently_building_session)

        return super().__get__(instance, owner)


@te.dataclass_transform(
    eq_default=False,
    field_specifiers=(internal_field, dataclasses.field),
)
class RioDataclassMeta(abc.ABCMeta):
    _observable_property_factory_: t.Callable[
        [str, introspection.types.TypeAnnotation, types.ModuleType, bool],
        ObservableProperty,
    ] = DataclassProperty
    _observable_properties_: dict[str, ObservableProperty]

    def __init__(
        cls,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        cls_vars = vars(cls)

        # We'll manually take care of calling __post_init__ methods because
        # dataclasses are unreliable. Rename the method so that it won't be
        # called by the dataclass constructor.
        if "__post_init__" in cls_vars:
            cls._rio_post_init = cls.__post_init__  # type: ignore
            del cls.__post_init__  # type: ignore

        # Apply the dataclass transform
        cls._preprocess_dataclass_fields()
        dataclasses.dataclass(eq=False, repr=False, match_args=False)(cls)
        cls._sanitize_init_signature()

        # Replace all properties with observable properties
        cls._initialize_observable_properties()

    def _preprocess_dataclass_fields(cls) -> None:
        # When a field has a default value (*not* default factory!), the
        # constructor actually doesn't assign the default value to the instance.
        # Instead, the default value is permanently stored in the class. So the
        # instance doesn't have the attribute, but the class does, and
        # everything is fine, right? Wrong. We create a `StateProperty` for each
        # field, which overrides that default value. We absolutely need every
        # attribute to be an instance attribute, which we can achieve by
        # replacing every default value with a default factory.
        #
        # We also need to create a RioField for each field.

        cls_vars = vars(cls)
        annotations = inspection.get_local_annotations(cls)

        local_fields: dict[str, RioField] = {}
        _FIELDS_BY_CLASS[cls] = local_fields

        rio_field: RioField

        for attr_name, annotation in annotations.items():
            if attr_name == "_" and annotation is dataclasses.KW_ONLY:
                continue

            # Skip `ClassVar` annotations
            if t.get_origin(annotation) is t.ClassVar:
                continue

            try:
                field_or_default = cls_vars[attr_name]
            except KeyError:
                rio_field = RioField()
            else:
                if not isinstance(field_or_default, dataclasses.Field):
                    rio_field = RioField(
                        default_factory=_make_default_factory_for_value(
                            field_or_default
                        ),
                        real_default_value=field_or_default,
                    )
                elif isinstance(field_or_default, RioField):
                    rio_field = field_or_default
                else:
                    rio_field = RioField.from_dataclass_field(field_or_default)

            setattr(cls, attr_name, rio_field)
            local_fields[attr_name] = rio_field

    def _sanitize_init_signature(cls) -> None:
        """
        Because we convert all default values to default factories, the
        signature of the `__init__` function gets messed up, which is a problem
        for our documentation. So we have to post-process the signature and
        replace all the <factory> defaults with the actual default values.
        """
        init_func = cls.__init__
        signature = inspect.signature(init_func)

        fields = all_class_fields(cls)

        parameters = list(signature.parameters.values())
        for i, parameter in enumerate(parameters):
            if repr(parameter.default) != "<factory>":
                continue

            try:
                field = fields[parameter.name]
            except KeyError:
                continue

            if field.real_default_value is dataclasses.MISSING:
                continue

            parameters[i] = parameter.replace(default=field.real_default_value)

        signature = signature.replace(parameters=parameters)
        init_func.__signature__ = signature  # type: ignore

    def _initialize_observable_properties(cls) -> None:
        """
        Spawn `ObservableProperty` instances for all annotated properties in
        this class.
        """
        all_properties: dict[str, ObservableProperty] = {}

        for base in reversed(cls.__bases__):
            if isinstance(base, __class__):
                all_properties.update(base._observable_properties_)

        cls._observable_properties_ = all_properties

        annotations: dict = vars(cls).get("__annotations__", {})
        module = sys.modules[cls.__module__]

        for field_name, field in class_local_fields(cls).items():
            # Skip internal fields
            if not field.create_property:
                continue

            # Create the StateProperty
            # readonly = introspection.typing.has_annotation(annotation, Readonly)
            readonly = False  # TODO

            prop = cls._observable_property_factory_(
                field_name, annotations[field_name], module, readonly
            )
            setattr(cls, field_name, prop)

            # Add it to the set of all state properties for rapid lookup
            cls._observable_properties_[field_name] = prop


@imy.docstrings.mark_as_private
class Dataclass(metaclass=RioDataclassMeta):
    # There isn't really a good type annotation for this... `te.Self` is the
    # closest thing
    def bind(self) -> te.Self:
        return AttributeBindingMaker(self)  # type: ignore
