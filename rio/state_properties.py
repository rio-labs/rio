from __future__ import annotations

import dataclasses
import types
import typing as t
import weakref

import introspection.typing
import revel

if t.TYPE_CHECKING:
    from .components import Component


__all__ = [
    "StateProperty",
    "AttributeBinding",
    "AttributeBindingMaker",
    "PendingAttributeBinding",
]


class StateProperty:
    """
    StateProperties act like regular properties, with additional considerations:

    - When a state property is assigned to, the component owning it is marked as
      dirty in the session

    - State properties have the ability to share their value with other state
      property instances. If state property `A` is assigned to state property
      `B`, then `B` creates a `StateBinding` and any future access to `B` will
      be routed to `A` instead:

    ```python
    class MyComponent(Component):
        foo_text = "Hello"

        def build(self) -> Component:
            return Bar(bar_text=self.bind().foo_text)  # Note `self.bind()` instead of `self`
    ```
    """

    def __init__(
        self,
        name: str,
        readonly: bool,
        raw_annotation: introspection.types.TypeAnnotation,
        module: types.ModuleType,
    ):
        self.name = name
        self.readonly = readonly

        self._module = module
        self._raw_annotation = raw_annotation
        self._resolved_annotation: introspection.typing.TypeInfo | None = None

    def _annotation_as_string(self) -> str:
        if isinstance(self._raw_annotation, str):
            return self._raw_annotation

        return introspection.typing.annotation_to_string(self._raw_annotation)

    def __get__(
        self,
        instance: Component | None,
        owner: type | None = None,
    ) -> object:
        # If accessed through the class, rather than instance, return the
        # StateProperty itself
        if instance is None:
            return self

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

    def __set__(self, instance: Component, value: object) -> None:
        if self.readonly:
            cls_name = type(instance).__name__
            raise AttributeError(
                f"Cannot assign to readonly property {cls_name}.{self.name}"
            )

        assert not isinstance(value, StateProperty), (
            f"You're still using the old attribute binding syntax for {instance} {self.name}"
        )

        instance._properties_assigned_after_creation_.add(self.name)

        # Look up the stored value
        instance_vars = vars(instance)
        try:
            local_value = instance_vars[self.name]
        except KeyError:
            # If no value is currently stored, that means this component is
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
                    "Attribute bindings can only be created when calling the component constructor"
                )

            # Delegate to the binding if it exists
            if isinstance(local_value, AttributeBinding):
                local_value.set_value(value)
                return

        # Otherwise set the value directly and mark the component as dirty
        instance_vars[self.name] = value

        instance._session_._register_dirty_component(
            instance,
            include_children_recursively=False,
        )

    def _create_attribute_binding(
        self,
        component: Component,
        request: PendingAttributeBinding,
    ) -> AttributeBinding:
        # In order to create a `StateBinding`, the owner's attribute
        # must also be a binding
        binding_owner = request._component_
        binding_owner_vars = vars(binding_owner)

        owner_binding = binding_owner_vars[request._state_property_.name]

        if not isinstance(owner_binding, AttributeBinding):
            owner_binding = AttributeBinding(
                owning_component_weak=weakref.ref(binding_owner),
                owning_property=self,
                is_root=True,
                parent=None,
                value=owner_binding,
                children=weakref.WeakSet(),
            )
            binding_owner_vars[request._state_property_.name] = owner_binding

        # Create the child binding
        child_binding = AttributeBinding(
            owning_component_weak=weakref.ref(component),
            owning_property=self,
            is_root=False,
            parent=owner_binding,
            value=None,
            children=weakref.WeakSet(),
        )
        owner_binding.children.add(child_binding)

        return child_binding

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.name}>"


@dataclasses.dataclass(eq=False)
class AttributeBinding:
    # Weak reference to the component containing this binding
    owning_component_weak: t.Callable[[], Component | None]

    # The state property whose value this binding is
    owning_property: StateProperty

    # Each binding is either the root-most binding, or a child of another
    # binding. This value is True if this binding is the root.
    is_root: bool

    parent: AttributeBinding | None
    value: object | None

    children: weakref.WeakSet[AttributeBinding] = dataclasses.field(
        default_factory=weakref.WeakSet
    )

    def get_value(self) -> object:
        if self.is_root:
            return self.value

        assert self.parent is not None
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
            owning_component = cur.owning_component_weak()

            if owning_component is not None:
                owning_component._session_._register_dirty_component(
                    owning_component,
                    include_children_recursively=False,
                )

            to_do.extend(cur.children)


class AttributeBindingMaker:
    """
    Helper class returned by `Component.bind()`. Used to create attribute
    bindings.
    """

    def __init__(self, component: Component):
        self.component = component

    def __getattribute__(self, name: str) -> object:
        component = super().__getattribute__("__dict__")["component"]
        component_cls = type(component)

        if name not in component_cls._state_properties_:
            raise AttributeError

        state_property = getattr(component_cls, name)
        return PendingAttributeBinding(component, state_property)


class PendingAttributeBinding:
    # This is not a dataclasses because it makes pyright do nonsense
    def __init__(self, component: Component, state_property: StateProperty):
        self._component_ = component
        self._state_property_ = state_property

    def _get_error_message(self, operation: str) -> str:
        return f"You attempted to use `{operation}` on a pending attribute binding. This is not supported. Attribute bindings are an instruction for rio to synchronize the state of two components. They do not have a value. For more information, see https://rio.dev/docs/howto/attribute-bindings"

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
        return f"<PendingAttributeBinding for {self._component_!r}.{self._state_property_.name}>"
