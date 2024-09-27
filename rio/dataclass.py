from __future__ import annotations

import abc
import copy
import dataclasses
import functools
import inspect
import typing as t

import typing_extensions as te

from . import inspection

__all__ = [
    "RioDataclassMeta",
    "RioField",
    "internal_field",
    "class_local_fields",
    "all_class_fields",
]


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


class RioField(dataclasses.Field):
    __slots__ = (
        "state_property",
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
        state_property: bool = True,
        serialize: bool = True,
    ):
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

        self.state_property = state_property
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
    # vscode doesn't understand default values, so the parameter that affect
    # static type checking (like `init`) must be explicitly passed in.
    init: bool,
    repr: bool = False,
    state_property: bool = False,
    serialize: bool = False,
) -> t.Any:
    return RioField(
        default=default,
        default_factory=default_factory,
        state_property=state_property,
        serialize=serialize,
        init=init,
        repr=repr,
    )


def _make_default_factory_for_value(value: T) -> t.Callable[[], T]:
    return functools.partial(copy.deepcopy, value)


@te.dataclass_transform(
    eq_default=False,
    field_specifiers=(internal_field, dataclasses.field),
)
class RioDataclassMeta(abc.ABCMeta):
    def __init__(cls, *args, **kwargs) -> None:
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
