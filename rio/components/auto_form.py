from __future__ import annotations

import dataclasses
import enum
import typing as t

import rio

from . import component, number_input, switch

__all__ = ["AutoForm"]


def prettify_name(name: str) -> str:
    parts = name.split("_")
    return " ".join(p.title() for p in parts)


@dataclasses.dataclass
class AutoFormChangeEvent:
    field_name: str
    value: t.Any


class AutoForm(component.Component):
    """
    TODO

    ## Metadata

    `public`: False
    """

    value: t.Any
    _: dataclasses.KW_ONLY
    on_change: rio.EventHandler[[AutoFormChangeEvent]] = None

    def __post_init__(self) -> None:
        # Make sure the passed value is a dataclass
        if not dataclasses.is_dataclass(self.value):
            raise TypeError(
                f"The value to `AutoForm` must be a dataclass, not `{type(self.value)}`"
            )

    async def _update_value(self, field_name: str, value: t.Any) -> None:
        # Update the value
        setattr(self, field_name, value)

        # Trigger the event
        await self.call_event_handler(
            self.on_change,
            AutoFormChangeEvent(
                field_name=field_name,
                value=value,
            ),
        )

    def _build_input_field(
        self,
        field_name: str,
        field_type: type,
    ) -> rio.Component:
        # Get sensible type information
        origin = t.get_origin(field_type)
        field_args = t.get_args(field_type)
        field_type = field_type if origin is None else origin
        del origin

        # Grab the value
        value = getattr(self.value, field_name)

        # `bool` -> `Switch`
        if field_type is bool:
            return switch.Switch(
                is_on=value,
                on_change=lambda e: self._update_value(field_name, e.is_on),
            )

        # `int` -> `NumberInput`
        if field_type is int:
            return number_input.NumberInput(
                value=value,
                decimals=0,
                on_change=lambda e: self._update_value(field_name, e.value),
            )

        # `float` -> `NumberInput`
        if field_type is float:
            return number_input.NumberInput(
                value=value,
                on_change=lambda e: self._update_value(field_name, e.value),
            )

        # `str` -> `TextInput`
        if field_type is str:
            return rio.TextInput(
                text=value,
                on_change=lambda e: self._update_value(field_name, e.text),
            )

        # `Literal` or `Enum` -> `Dropdown`
        if field_type is t.Literal or issubclass(field_type, enum.Enum):
            if field_type is t.Literal:
                mapping = {str(a): a for a in field_args}
            else:
                field_type = t.cast(t.Type[enum.Enum], field_type)
                mapping = {prettify_name(f.name): f.value for f in field_type}

            return rio.Dropdown(
                mapping,
                selected_value=value,
                on_change=lambda e: self._update_value(field_name, e.value),
            )

        # Unsupported type
        raise TypeError(
            f"AutoForm does not support fields of type `{field_type}`"
        )

    def build(self) -> rio.Component:
        grid = rio.Grid(
            row_spacing=0.5,
            column_spacing=1,
        )

        # Iterate over the class' fields and build the input fields
        for ii, field in enumerate(dataclasses.fields(self.value)):
            field_py_name = field.name
            field_type = field.type
            field_nicename = prettify_name(field_py_name)

            # Skip fields that are not supported
            try:
                input_component = self._build_input_field(
                    field_py_name,
                    field_type,  # type: ignore
                )
            except TypeError:
                continue

            # Add a label
            grid.add(
                rio.Text(text=field_nicename, selectable=False, align_x=0),
                ii,
                0,
            )

            # And a input field
            grid.add(input_component, ii, 1)

        return grid
