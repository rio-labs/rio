from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings
from uniserde import JsonDoc

import rio

from .. import utils
from .component import AccessibilityRole, Key
from .keyboard_focusable_components import KeyboardFocusableFundamentalComponent

__all__ = [
    "Dropdown",
    "DropdownChangeEvent",
]

T = t.TypeVar("T")


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class DropdownChangeEvent(t.Generic[T]):
    """
    Holds information regarding a dropdown change event.

    This is a simple dataclass that stores useful information for when the user
    selects an option in a `Dropdown`. You'll typically receive this as argument
    in `on_change` events.

    ## Attributes

    `value`: The new `selected_value` of the `Dropdown`.
    """

    value: T


@t.final
class Dropdown(KeyboardFocusableFundamentalComponent, t.Generic[T]):
    """
    A dropdown menu for selecting from one of several options.

    Dropdowns present the user with a list of options, allowing them to select
    exactly one. In their default state dropdowns are compact and display the
    currently selected option. When activated, a popup menu appears with a list
    of all options. Typing while the dropdown is opened will filter the options.

    ## Attributes

    `options`: A mapping from option names to values. The names are displayed
        in the dropdown menu, and the corresponding value is returned when
        the user selects the option. The values must be comparable.

    `label`: A short text to display next to the dropdown.

    `style`: Changes the visual appearance of the text input.

    `selected_value`: The value of the currently selected option.

    `is_sensitive`: Whether the dropdown should respond to user input.

    `is_valid`: Visually displays to the user whether the current option is
        valid. You can use this to signal to the user that their input needs
        to be changed.

    `on_change`: Triggered whenever the user selects an option.


    ## Examples

    Here's a simple example that allows the user to select an option and
    displays it back to them:

    ```python
    class MyComponent(rio.Component):
        selected_value: str = "a"

        def build(self) -> rio.Component:
            return rio.Column(
                rio.Dropdown(
                    options={
                        "Option A": "a",
                        "Option B": "b",
                        "Option C": "c",
                    },
                    # In order to retrieve a value from the component, we'll
                    # use an attribute binding. This way our own value will
                    # be updated whenever the user changes the text.
                    selected_value=self.bind().selected_value,
                    label="Enter a Text",
                ),
                rio.Text(f"You've chosen {self.selected_value}"),
            )
    ```

    Alternatively you can also attach an event handler to react to changes. This
    is a little more verbose, but allows you to run arbitrary code when the user
    selects an option:

    ```python
    class MyComponent(rio.Component):
        selected_value: str = "a"

        def on_value_change(self, event: rio.DropdownChangeEvent):
            # This function will be called whenever the user selects an. We'll
            # display the new selection in addition to updating our own
            # attribute.
            self.selected_value = event.value
            print(f"You've chosen {self.selected_value}")

        def build(self) -> rio.Component:
            return rio.Dropdown(
                options={
                    "Option A": "a",
                    "Option B": "b",
                    "Option C": "c",
                },
                selected_value=self.selected_value,
                label="Enter a Text",
                on_change=self.on_value_change,
            )
    ```
    """

    options: t.Mapping[str, T]
    _: dataclasses.KW_ONLY
    label: str
    style: t.Literal["underlined", "rounded", "pill"]
    selected_value: T | utils.NotGiven = utils.NOT_GIVEN
    is_sensitive: bool
    is_valid: bool
    on_change: rio.EventHandler[DropdownChangeEvent[T]]

    def __init__(
        self,
        options: t.Mapping[str, T] | t.Sequence[T],
        *,
        label: str = "",
        style: t.Literal["underlined", "rounded", "pill"] = "underlined",
        selected_value: T | None = None,
        on_change: rio.EventHandler[DropdownChangeEvent[T]] = None,
        is_sensitive: bool = True,
        is_valid: bool = True,
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
    ):
        if len(options) == 0:
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
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
            align_x=align_x,
            align_y=align_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
            accessibility_role=accessibility_role,
        )

        if not isinstance(options, t.Mapping):
            options = {str(value): value for value in options}

        self.options = options
        self.label = label
        self.style = style
        self.on_change = on_change
        self.is_sensitive = is_sensitive
        self.is_valid = is_valid

        # This is an unsafe assignment, because the value could be `None`. This
        # will be fixed in `__post_init__`, once the attribute bindings have been
        # initialized.
        self.selected_value = selected_value  # type: ignore

    def __post_init__(self) -> None:
        # Make sure a value is selected
        if isinstance(self.selected_value, utils.NotGiven):
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

    def _custom_serialize_(self) -> JsonDoc:
        result: JsonDoc = {
            "optionNames": list(self.options.keys()),
            "selectedName": self._fetch_selected_name(),
        }

        return result

    async def _on_message_(self, msg: t.Any) -> None:
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
        assert not isinstance(self.selected_value, utils.NotGiven), (
            self.selected_value
        )

        await self.call_event_handler(
            self.on_change, DropdownChangeEvent(self.selected_value)
        )


Dropdown._unique_id_ = "Dropdown-builtin"
