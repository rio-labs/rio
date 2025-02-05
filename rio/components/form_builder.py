from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings

import rio

from . import component, number_input, switch

__all__ = [
    "FormBuilder",
]

T = t.TypeVar("T")


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class FormChangeEvent:
    """
    Holds information regarding a FormBuilder's change event.

    This is a simple dataclass that stores useful information for when the user
    changes a value in a `FormBuilder`. You'll typically receive this as
    argument in `on_change` events.

    ## Attributes

    `key`: They key of the component that has changed.

    `is_valid`: Whether all values in the form builder are now valid.

    `validation_error`: This is `None` if the form is valid, otherwise it
        contains a string with the error message.
    """

    key: int | str | None

    is_valid: bool

    validation_error: None | str


class FormBuilder(component.Component):
    """
    TODO

    ## Metadata

    `public`: False
    """

    _: dataclasses.KW_ONLY

    heading: str | None = None
    heading_style: t.Literal["heading1", "heading2", "heading3"] = "heading2"

    is_valid: bool = True
    validation_error: None | str = None

    on_change: rio.EventHandler[[FormChangeEvent]] = None

    # All fields in the form are added to this list. Each entry is a tuple
    # of
    #
    # - The component to display for the field
    # - The key of the field
    # - The validation function
    # - A function to call when the field changes
    #
    # The index in the field is used as unique identifier for the field.
    _all_fields: list[
        tuple[
            rio.Component,
            int | str | None,
            t.Callable[[t.Any], str | None] | None,
            rio.EventHandler[t.Any],
        ]
    ] = dataclasses.field(
        default_factory=list,
        init=False,
    )

    # Maps field indices to their validation errors, if any. If no errors
    # show up in here the form is valid.
    _all_errors: dict[int, str] = dataclasses.field(
        default_factory=dict,
        init=False,
    )

    async def _on_change(self, field_index: int, new_value: t.Any) -> None:
        """
        Call this whenever a value has changed. It will re-run the validator and
        trigger events as appropriate.
        """
        # Get information about this field
        _, key, validator, field_change_handler = self._all_fields[field_index]

        # Re-validate the form
        if validator is None:
            validation_error = None
        else:
            validation_error = validator(new_value)

        # Update the validation state
        if validation_error is None:
            self._all_errors.pop(field_index, None)

            if self._all_errors:
                self.validation_error = next(iter(self._all_errors.values()))
            else:
                self.validation_error = None
        else:
            self._all_errors[field_index] = validation_error
            self.validation_error = validation_error

        self.is_valid = self.validation_error is None

        # Trigger the field's change handler
        await self.call_event_handler(field_change_handler, new_value)

        # Trigger the form's change event
        await self.call_event_handler(
            self.on_change,
            FormChangeEvent(
                key=key,
                is_valid=self.is_valid,
                validation_error=self.validation_error,
            ),
        )

    def _add_custom_field(
        self,
        component: rio.Component,
        key: int | str | None,
        validate: t.Callable[[T], str | None] | None,
        on_change: rio.EventHandler[T],
    ) -> int:
        """
        Adds a field to the form builder. Returns the index of the field.
        """
        self._all_fields.append((component, key, validate, on_change))
        return len(self._all_fields) - 1

    def _add_labelled_field(
        self,
        label: str,
        value_component: rio.Component,
        key: int | str | None,
        validate: t.Callable[[T], str | None] | None,
        on_change: rio.EventHandler[T],
    ) -> int:
        """
        Adds a component in "standard style". This will have a text label added
        as well as the component itself.
        """
        # Create the component
        column = rio.Row(
            rio.Text(label),
            value_component,
            spacing=1,
        )

        # Add the component
        self._all_fields.append((column, key, validate, on_change))
        return len(self._all_fields) - 1

    def add_bool(
        self,
        label: str,
        value: bool,
        *,
        style: t.Literal["switch", "checkbox"] = "switch",
        key: int | str | None = None,
        validate: t.Callable[[bool], str | None] | None = None,
        on_change: rio.EventHandler[bool] = None,
    ) -> None:
        """
        Adds a boolean field to the form.

        This adds a field to the form that allows the user to toggle a boolean
        value. You can choose between a switch or a checkbox style.

        ## Parameters

        `label`: The label to display next to the field.

        `value`: The initial value of the field. Use `self.bind().value` to
            automatically receive changes from this field.

        `style`: How to display the field. You can choose between a "switch" or
            "checkbox" style.

        `key`: A unique key for this field. This is useful if you want to
            identify the field when the form changes.

        `validate`: A function that validates the value. This should return a
            string with an error message if the value is invalid, otherwise
            `None`.

        `on_change`: A function that is called whenever the value changes. This
            function receives the new value as argument.
        """

        # Create the component
        index = len(self._all_fields)

        if style == "switch":
            component = switch.Switch(
                is_on=value,
                on_change=lambda e: self._on_change(index, e.is_on),
            )
        elif style == "checkbox":
            component = rio.Checkbox(
                is_on=value,
                on_change=lambda e: self._on_change(index, e.is_on),
            )
        else:
            raise ValueError(f"Invalid style: {style}")

        # Add the component
        self._add_labelled_field(
            label,
            component,
            key,
            validate,
            on_change,
        )

    def add_number(
        self,
        label: str,
        value: int | float,
        *,
        decimals: int = 2,
        key: int | str | None = None,
        validate: t.Callable[[int | float], str | None] | None = None,
        on_change: rio.EventHandler[int | float] = None,
    ) -> None:
        # Create the component
        index = len(self._all_fields)

        component = number_input.NumberInput(
            value=value,
            decimals=decimals,
            on_change=lambda e: self._on_change(index, e.value),
        )

        # Add the component
        self._add_labelled_field(
            label,
            component,
            key,
            validate,
            on_change,
        )

    def build(self) -> rio.Component:
        column = rio.Column(
            spacing=1,
        )

        # Heading, if any
        if self.heading is not None:
            column.add(
                rio.Text(
                    self.heading,
                    style=self.heading_style,
                ),
            )

        # Add all fields to the column
        for component, *_ in self._all_fields:
            column.add(component)

        # Done
        return column
