from __future__ import annotations

import abc
import dataclasses
import types
import typing as t
import weakref

import introspection.typing
import revel

import rio

from .. import global_state

__all__ = [
    "ObservableProperty",
    "AttributeBinding",
    "AttributeBindingMaker",
    "PendingAttributeBinding",
]

T = t.TypeVar("T")


class ObservableProperty(abc.ABC, t.Generic[T]):
    """
    ObservableProperties do the following things:

    - Track reads and writes
    - Enable attribute bindings

    They're the cornerstone of Rio's declarative programming model. Attribute
    bindings allow easy sharing of values between different instances, and
    tracking access allows Rio to figure out when components need to be rebuilt.

    This is a generic class. An `ObservableProperty[T]` can be applied to
    instances of class T. It is also an abstract class. Given an object of type
    T, the abstract method `_get_affected_sessions()` must return all
    `rio.Session`s that might be affected by a read/write to this property.
    """

    def __init__(
        self,
        name: str,
        raw_annotation: introspection.types.TypeAnnotation,
        forward_ref_context: types.ModuleType,
        readonly: bool = False,
    ):
        self.name = name
        self.readonly = readonly

        self._raw_annotation = raw_annotation
        self._forward_ref_context = forward_ref_context
        self._resolved_annotation: (
            introspection.types.TypeAnnotation | t.Literal[""]
        ) = ""  # Empty string means "not set"

    def _annotation_as_string(self) -> str:
        """
        Used in debug mode to output an error message if the assigned value
        doesn't match the type annotation.
        """
        if isinstance(self._raw_annotation, str):
            return self._raw_annotation

        return introspection.typing.annotation_to_string(self._raw_annotation)

    @abc.abstractmethod
    def _get_affected_sessions(self, instance: T, /) -> t.Iterable[rio.Session]:
        raise NotImplementedError

    def __set_name__(self, owner: type, name: str):
        self.name = name

    def __get__(
        self,
        instance: T | None,
        owner: type | None = None,
    ) -> object:
        # If accessed through the class, rather than instance, return the
        # ObservableProperty itself
        if instance is None:
            return self

        global_state.accessed_attributes[instance].add(self.name)

        # Otherwise get the value assigned to the property in the component
        # instance
        try:
            value = vars(instance)[self.name]
        except KeyError:
            raise AttributeError(self.name) from None

        # If the value is a binding return the binding's value
        if isinstance(value, AttributeBinding):
            return value.get_value()

        # Otherwise return the value
        return value

    def _on_value_change(self, instance: T, /) -> None:
        for session in self._get_affected_sessions(instance):
            session._changed_attributes[instance].add(self.name)
            session._refresh_required_event.set()

    def __set__(self, instance: T, value: object) -> None:
        if self.readonly:
            cls_name = type(instance).__name__
            raise AttributeError(
                f"Cannot assign to readonly property {cls_name}.{self.name}"
            )

        # Look up the stored value
        instance_vars = vars(instance)
        try:
            local_value = instance_vars[self.name]
        except KeyError:
            # If no value is currently stored, that means this instance is
            # currently being instantiated. We may have to create a state
            # binding.
            if isinstance(value, PendingAttributeBinding):
                value = self._create_attribute_binding(instance, value)
        else:
            # If a value is already stored, that means this is a re-assignment.
            # Which further means it's an assignment outside of `__init__`.
            # Which is not a valid place to create a attribute binding.
            if isinstance(value, PendingAttributeBinding):
                raise RuntimeError(
                    "Attribute bindings can only be created by calling the constructor"
                )

            # Delegate to the binding if it exists
            if isinstance(local_value, AttributeBinding):
                local_value.set_value(value)
                return

        # Otherwise set the value directly and mark the component as dirty
        instance_vars[self.name] = value

        self._on_value_change(instance)

    def _create_attribute_binding(
        self,
        instance: T,
        request: PendingAttributeBinding,
    ) -> AttributeBinding:
        if self.readonly:
            raise AttributeError(
                f"{type(instance).__name__}.{self.name!r} is read-only. It cannot be used in an attribute binding."
            )

        # In order to create an `AttributeBinding`, the owner's attribute must
        # also be a binding
        binding_owner = request._instance_
        binding_owner_vars = vars(binding_owner)

        owner_binding = binding_owner_vars[request._property_.name]

        if not isinstance(owner_binding, AttributeBinding):
            owner_binding = AttributeBinding(
                owning_instance_weak=weakref.ref(binding_owner),
                owning_property=request._property_,
                parent=None,
                value=owner_binding,
                children=weakref.WeakSet(),
            )
            binding_owner_vars[request._property_.name] = owner_binding

        # Create the child binding
        child_binding = AttributeBinding(
            owning_instance_weak=weakref.ref(instance),
            owning_property=self,
            parent=owner_binding,
            value=None,
            children=weakref.WeakSet(),
        )
        owner_binding.children.add(child_binding)

        return child_binding

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.name!r}>"


@dataclasses.dataclass(eq=False)
class AttributeBinding:
    # Weak reference to the component containing this binding
    owning_instance_weak: t.Callable[[], object | None]

    # The state property whose value this binding is
    owning_property: ObservableProperty

    # Each binding is either the root-most binding, or a child of another
    # binding. For the root-most binding, the `parent` is None.
    parent: AttributeBinding | None

    value: object | None

    children: weakref.WeakSet[AttributeBinding] = dataclasses.field(
        default_factory=weakref.WeakSet
    )

    def get_value(self) -> object:
        if self.parent is None:
            return self.value

        return self.parent.get_value()

    def set_value(self, value: object) -> None:
        # Delegate to the parent, if any
        if self.parent is not None:
            self.parent.set_value(value)
            return

        # Otherwise this is the root-most binding. Set the value
        self.value = value

        # Then recursively mark all children as dirty
        self.recursively_mark_children_as_dirty()

    def recursively_mark_children_as_dirty(self) -> None:
        to_do: list[AttributeBinding] = [self]

        while to_do:
            cur = to_do.pop()
            owning_instance = cur.owning_instance_weak()

            if owning_instance is not None:
                owning_property: ObservableProperty = cur.owning_property  # type: ignore (it's incorrectly treating `owning_property` as a descriptor)
                owning_property._on_value_change(owning_instance)

            to_do.extend(cur.children)


class AttributeBindingMaker:
    """
    Helper class returned by `RioDataclass.bind()`. Used to create attribute
    bindings.
    """

    def __init__(self, instance: rio.Dataclass):
        self.instance = instance

    def __getattribute__(self, name: str) -> object:
        instance: rio.Dataclass = super().__getattribute__("__dict__")[
            "instance"
        ]
        instance_cls = type(instance)

        try:
            prop = instance_cls._observable_properties_[name]
        except KeyError:
            raise AttributeError(
                f"{instance!r} has no attribute {name!r}"
            ) from None

        if prop.readonly:
            raise AttributeError(
                f"{instance_cls.__name__}.{name!r} is read-only. It cannot be used in an attribute binding."
            )

        return PendingAttributeBinding(instance, prop)


class PendingAttributeBinding:
    # This is not a dataclass because it makes pyright do nonsense
    def __init__(self, instance: rio.Dataclass, prop: ObservableProperty):
        self._instance_ = instance
        self._property_ = prop

    def _get_error_message(self, operation: str) -> str:
        return f"You attempted to use `{operation}` on a pending attribute binding. This is not supported. Attribute bindings are an instruction for Rio to synchronize the state of two components. They do not have a value. For more information, see https://rio.dev/docs/howto/attribute-bindings"

    def _warn_about_incorrect_usage(self, operation: str) -> None:
        revel.warning(self._get_error_message(operation))

    def __getattr__(self, name: str):
        operation = f".{name}"
        self._warn_about_incorrect_usage(operation)
        raise AttributeError(self._get_error_message(operation))

    def __getitem__(self, item: object):
        operation = f"[{item!r}]"
        self._warn_about_incorrect_usage(operation)
        raise TypeError(self._get_error_message(operation))

    def __add__(self, other):
        self._warn_about_incorrect_usage("+")
        return NotImplemented

    def __sub__(self, other):
        self._warn_about_incorrect_usage("-")
        return NotImplemented

    def __mul__(self, other):
        self._warn_about_incorrect_usage("*")
        return NotImplemented

    def __div__(self, other):
        self._warn_about_incorrect_usage("//")
        return NotImplemented

    def __truediv__(self, other):
        self._warn_about_incorrect_usage("/")
        return NotImplemented

    def __call__(self, other):
        self._warn_about_incorrect_usage("__call__")
        raise TypeError(f"{type(self).__name__} objects are not callable")

    def __repr__(self) -> str:
        self._warn_about_incorrect_usage("__repr__")
        return f"<PendingAttributeBinding for {self._instance_!r}.{self._property_.name}>"
