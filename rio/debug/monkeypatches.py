import typing as t
from pathlib import Path

import introspection.typing

from .. import components, global_state
from ..components.component import Component, ComponentMeta
from ..observables.component_property import ComponentProperty
from ..observables.observable_property import (
    ObservableProperty,
    PendingAttributeBinding,
)

__all__ = [
    "apply_monkeypatches",
]


def apply_monkeypatches() -> None:
    """
    Enables extra safeguards that are too slow to be enabled permanently. Used
    by `rio run` when running in debug mode.
    """
    introspection.wrap_method(Component_bind, Component, "bind")
    introspection.wrap_method(ComponentMeta_call, ComponentMeta, "__call__")
    introspection.wrap_method(
        ComponentProperty_get, ComponentProperty, "__get__"
    )
    introspection.wrap_method(
        ObservableProperty_set, ObservableProperty, "__set__"
    )
    introspection.wrap_method(LinearContainer_init, components.Row, "__init__")
    introspection.wrap_method(
        LinearContainer_init, components.Column, "__init__"
    )
    introspection.wrap_method(ListView_init, components.ListView, "__init__")


def Component_bind(wrapped_method, self: Component):
    if global_state.currently_building_session is None:
        raise RuntimeError(
            "`.bind()` can only be called inside of the `build()` method"
        )

    if global_state.currently_building_component is not self:
        raise RuntimeError("`.bind()` can only be called on `self`")

    return wrapped_method(self)


def ComponentMeta_call(wrapped_method, cls, *args, **kwargs):
    component: Component = wrapped_method(cls, *args, **kwargs)

    # Make sure the component was properly initialized
    try:
        component._properties_set_by_creator_
    except AttributeError:
        raise Exception(
            f"The component {component} wasn't initialized properly. If you"
            f" have written a custom `__init__` method, make sure to call"
            f" `super().__init__()`"
        ) from None

    # Keep track of who created this component
    with introspection.CallFrame.up(2) as frame:
        component._creator_stackframe_ = (
            Path(frame.file_name),
            frame.current_line_number,
        )

    # Track whether this instance is internal to Rio. This is the case if
    # this component's creator is defined in Rio.
    creator = global_state.currently_building_component
    if creator is None:
        assert type(component).__qualname__ == "HighLevelRootComponent", type(
            component
        ).__qualname__
        component._rio_internal_ = True
    else:
        component._rio_internal_ = creator._rio_builtin_

    return component


def ComponentProperty_get(
    wrapped_method,
    self: ComponentProperty,
    instance: Component | None,
    owner=None,
):
    if instance is None:
        return self

    if not instance._init_called_:
        raise RuntimeError(
            f"The `__init__` method of {instance} attempted to access the state"
            f" property {self.name!r}. This is not allowed. `__init__` methods"
            f" must only *set* properties, not *read* them. Move the code that"
            f" needs to read a state property into the `__post_init__` method."
        )

    return wrapped_method(self, instance, owner)


def ObservableProperty_set(
    wrapped_method,
    self: ObservableProperty,
    instance: object,
    value: object,
) -> None:
    # Type check the value
    if not isinstance(value, PendingAttributeBinding):
        if self._resolved_annotation == "":
            type_info = introspection.typing.TypeInfo(
                self._raw_annotation,
                forward_ref_context=self._forward_ref_context,
                treat_name_errors_as_imports=True,
            )

            # If it's a generic type, give it its type arguments back. This is
            # especially important in case of special typing constructs such as
            # `Optional` and `Union`.
            if type_info.arguments is None:
                self._resolved_annotation = type_info.type
            else:
                self._resolved_annotation = introspection.typing.parameterize(
                    type_info.type, type_info.arguments
                )

        try:
            valid = introspection.typing.is_instance(
                value, self._resolved_annotation
            )
        except introspection.errors.CannotResolveForwardref as error:
            # revel.warning(
            #     f"Unable to verify assignment of {value!r} to"
            #     f" {type(instance).__qualname__}.{self.name} (annotated as"
            #     f" {self._annotation_as_string()}) because the forward"
            #     f" reference {error.forward_ref!r} cannot be resolved",
            #     markup=False,
            # )
            pass
        except NotImplementedError:
            # revel.warning(
            #     f"Unable to verify assignment of {value!r} to"
            #     f" {type(instance).__qualname__}.{self.name} (annotated as"
            #     f" {self._annotation_as_string()})",
            #     markup=False,
            # )
            pass
        else:
            if not valid:
                raise TypeError(
                    f"The value {value!r} can't be assigned to"
                    f" {type(instance).__qualname__}.{self.name}, which is"
                    f" annotated as {self._annotation_as_string()}"
                )

    # Chain to the original method
    wrapped_method(self, instance, value)


def LinearContainer_init(
    wrapped_method,
    self: components.Row,
    *children,
    proportions: t.Literal["homogeneous"] | t.Sequence[float] | None = None,
    **kwargs,
) -> None:
    # Proportions related checks
    if proportions is not None and not isinstance(proportions, str):
        proportions = list(proportions)

        # Make sure the number of proportions matches the number of children
        if len(proportions) != len(children):
            if len(proportions) == 1:
                proportions_str = f"one proportion was {proportions}"
            else:
                proportions_str = f"{len(proportions)} proportions were"

            raise ValueError(
                f"The component has {len(children)} children, but {proportions_str} provided."
            )

        # The sum of all proportions must exceed 0
        if proportions and sum(proportions) <= 0:
            # TODO: While this handles a length of zero children fine, JS
            # probably doesn't!
            raise ValueError(
                "The sum of all proportions must be greater than 0."
            )

        # Every proportion must be positive
        for proportion in proportions:
            if proportion < 0:
                raise ValueError(
                    f"{proportion} is not a valid proportion. All proportions must be greater than or equal to zero."
                )

    # Chain to the original method
    wrapped_method(
        self,
        *children,
        proportions=proportions,
        **kwargs,
    )


def ListView_init(
    wrapped_method,
    self: components.ListView,
    *children,
    **kwargs,
) -> None:
    # Make sure all children have a key set
    assert isinstance(children, tuple), children

    for child in children:
        if child.key != None or isinstance(child, components.SeparatorListItem):
            continue

        raise ValueError(
            f"ListView child {child!r} has no key set. List items change frequently, and are often reshuffled. This can lead to unexpected reconciliations, and slow down the UI."
        )

    # Chain to the original method
    wrapped_method(self, *children, **kwargs)
