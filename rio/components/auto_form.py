from __future__ import annotations

import dataclasses
import enum
from dataclasses import KW_ONLY, dataclass, is_dataclass
from typing import *  # type: ignore

import rio

from . import component, number_input, switch

__all__ = ["AutoForm"]


def prettify_name(name: str) -> str:
    parts = name.split("_")
    return " ".join(p.title() for p in parts)


@dataclass
class AutoFormChangeEvent:
    field_name: str
    value: Any


class AutoForm(component.Component):
    """
    ## Metadata

    public: False
    """

    # TODO
    value: Any
    _: KW_ONLY
    on_change: rio.EventHandler[[AutoFormChangeEvent]] = None

    def __post_init__(self) -> None:
        # Make sure the passed value is a dataclass
        if not is_dataclass(self.value):
            raise TypeError(
                f"The value to `AutoForm` must be a dataclass, not `{type(self.value)}`"
            )

    async def _update_value(self, field_name: str, value: Any) -> None:
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
        origin = get_origin(field_type)
        field_args = get_args(field_type)
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
        if field_type is Literal or issubclass(field_type, enum.Enum):
            if field_type is Literal:
                mapping = {str(a): a for a in field_args}
            else:
                field_type = cast(Type[enum.Enum], field_type)
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
                    field_py_name, field_type
                )
            except TypeError:
                continue

            # Add a label
            grid.add(
                rio.Text(text=field_nicename, align_x=0),
                ii,
                0,
            )

            # And a input field
            grid.add(input_component, ii, 1)

        return grid
