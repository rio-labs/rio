from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import KW_ONLY, dataclass
from typing import Any, Generic, Literal, TypeVar, final

from uniserde import JsonDoc

import rio.docs

from .fundamental_component import FundamentalComponent

__all__ = [
    "Dropdown",
    "DropdownChangeEvent",
]

T = TypeVar("T")


@final
@rio.docs.mark_constructor_as_private
@dataclass
class DropdownChangeEvent(Generic[T]):
    """
    Holds information regarding a dropdown change event.

    This is a simple dataclass that stores useful information for when the user
    selects an option in a `Dropdown`. You'll typically receive this as argument
    in `on_change` events.

    ## Attributes

    `value`: The new `selected_value` of the `Dropdown`.
    """

    value: T


@final
class Dropdown(FundamentalComponent, Generic[T]):
    """
    A dropdown menu allowing the user to select one of several options.

    Dropdowns present the user with a list of options, allowing them to select
    exactly one. In their default state dropdowns are compact and display the
    currently selected option. When activated, a popup menu appears with a list
    of all available options.


    ## Attributes

    `options`: A mapping from option names to values. The names are displayed
        in the dropdown menu, and the corresponding value is returned when
        the user selects the option. The values must be comparable.

    `label`: A short text to display next to the dropdown.

    `selected_value`: The value of the currently selected option.

    `is_sensitive`: Whether the dropdown should respond to user input.

    `is_valid`: Visually displays to the user whether the current option is
        valid. You can use this to signal to the user that their input needs
        to be changed.

    `on_change`: Triggered whenever the user selects an option.


    ## Examples

    This minimal example will simply display a dropdown with three options:

    ```python
    rio.Dropdown(["a", "b", "c"])
    ```

    In a `Component` class, you can use attribute bindings to keep your input
    value updated and track any changes. Here's a quick example with a
    `Dropdown`:

    ```python
    class MyComponent(rio.Component):
        value: str = "b"

        def build(self) -> rio.Component:
            return rio.Dropdown(
                options=["a", "b", "c"],
                label="Dropdown",
                selected_value=self.bind().value,  # Attribute binding
                on_change=lambda event: print(event.value),
            )
    ```

    If you want to do more than e.g. just print a message, you can use a method
    call instead of a lambda function:

    ```python
    class MyComponent(rio.Component):
        value: str = "b"

        def on_change_update_value(self, event: rio.DropdownChangeEvent):
            # You can do whatever you want in this method like update the value
            # and print it
            self.value = event.value
            print(event.value)

        def build(self) -> rio.Component:
            return rio.Dropdown(
                options=["a", "b", "c"],
                label="Dropdown",
                selected_value=self.value,
                on_change=self.on_change_update_value,
            )
    ```
    """

    options: Mapping[str, T]
    _: KW_ONLY
    label: str
    selected_value: T
    is_sensitive: bool
    is_valid: bool
    on_change: rio.EventHandler[DropdownChangeEvent[T]]

    def __init__(
        self,
        options: Mapping[str, T] | Sequence[T],
        *,
        label: str = "",
        selected_value: T | None = None,
        on_change: rio.EventHandler[DropdownChangeEvent[T]] = None,
        is_sensitive: bool = True,
        is_valid: bool = True,
        key: str | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        width: float | Literal["natural", "grow"] = "natural",
        height: float | Literal["natural", "grow"] = "natural",
        align_x: float | None = None,
        align_y: float | None = None,
    ):
        if not options:
            raise ValueError("`Dropdown` must have at least one option.")

        super().__init__(
            key=key,
            margin=margin,
            margin_x=margin_x,
            margin_y=margin_y,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            width=width,
            height=height,
            align_x=align_x,
            align_y=align_y,
        )

        if isinstance(options, Sequence):
            options = {str(value): value for value in options}

        self.options = options
        self.label = label
        self.on_change = on_change
        self.is_sensitive = is_sensitive
        self.is_valid = is_valid

        # This is an unsafe assignment, because the value could be `None`. This
        # will be fixed in `__post_init__`, once the attribute bindings have been
        # initialized.
        self.selected_value = selected_value  # type: ignore

    def __post_init__(self) -> None:
        # Make sure a value is selected
        if self.selected_value is None:
            self.selected_value = next(iter(self.options.values()))

    def _fetch_selected_name(self) -> str:
        # The frontend works with names, not values. Get the corresponding
        # name.

        # Avoid hammering a potential attribute binding
        selected_value = self.selected_value

        # Fetch the name
        for name, value in self.options.items():
            if value == selected_value:
                return name
        else:
            # If nothing matches, just select the first option
            return next(iter(self.options.keys()))

    def _custom_serialize(self) -> JsonDoc:
        result: JsonDoc = {
            "optionNames": list(self.options.keys()),
            "selectedName": self._fetch_selected_name(),
        }

        return result

    async def _on_message(self, msg: Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg

        # The frontend works with names, not values. Get the corresponding
        # value.
        try:
            selected_value = self.options[msg["name"]]
        except KeyError:
            # Invalid names may be sent due to lag between the frontend and
            # backend. Ignore them.
            return

        self._apply_delta_state_from_frontend(
            {"selected_value": selected_value}
        )

        # Trigger the event
        await self.call_event_handler(
            self.on_change, DropdownChangeEvent(self.selected_value)
        )

        # Refresh the session
        await self.session._refresh()


Dropdown._unique_id = "Dropdown-builtin"
