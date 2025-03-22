from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings
from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Checkbox",
    "CheckboxChangeEvent",
]


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class CheckboxChangeEvent:
    """
    Holds information regarding a checkbox change event.

    This is a simple dataclass that stores useful information for when the user
    switches a `Checkbox` on or off. You'll typically receive this as argument
    in `on_change` events.

    ## Attributes

    `is_on`: Whether the checkbox is now ticked.
    """

    is_on: bool


@t.final
class Checkbox(FundamentalComponent):
    """
    An input for `True` / `False` values.

    Checkboxes allow the user to toggle between an "on" and an "off" state and
    effectively correspond to a Python `bool` value. Use them to allow the user
    to enable or disable certain features, or to select between two options.

    These are very similar to the `Switch` component, but their visuals can
    sometimes be preferable depending on the context.


    ## Attributes

    `is_on`: Whether the Checkbox is currently in the "on" state.

    `is_sensitive`: Whether the Checkbox should respond to user input.

    `on_change`: Triggered when the user toggles the Checkbox.


    ## Examples

    Here's a simple example that allows the user to turn a Checkbox on and off and
    displays the current state:

    ```python
    class MyComponent(rio.Component):
        is_on: bool = False

        def build(self) -> rio.Component:
            return rio.Column(
                rio.Checkbox(
                    # In order to retrieve a value from the component, we'll
                    # use an attribute binding. This way our own value will
                    # be updated whenever the user changes the text.
                    is_on=self.bind().is_on,
                ),
                rio.Text("ON" if self.is_on else "Off"),
            )
    ```

    Alternatively you can also attach an event handler to react to changes. This
    is a little more verbose, but allows you to run arbitrary code when the user
    changes the text:

    ```python
    class MyComponent(rio.Component):
        is_on: bool = False

        def on_value_change(self, event: rio.CheckboxChangeEvent):
            # This function will be called whenever the input's value
            # changes. We'll display the new value in addition to updating
            # our own attribute.
            self.is_on = event.is_on
            print("The Checkbox is now", "ON" if self.is_on else "Off")

        def build(self) -> rio.Component:
            return rio.Checkbox(
                is_on=self.is_on,
                on_change=self.on_value_change,
            )
    ```
    """

    is_on: bool = False
    _: dataclasses.KW_ONLY
    is_sensitive: bool = True
    on_change: rio.EventHandler[CheckboxChangeEvent] = None

    def _validate_delta_state_from_frontend(self, delta_state: JsonDoc) -> None:
        if not set(delta_state) <= {"is_on"}:
            raise AssertionError(
                f"Frontend tried to change `{type(self).__name__}` state: {delta_state}"
            )

        if "is_on" in delta_state and not self.is_sensitive:
            raise AssertionError(
                f"Frontend tried to set `Checkbox.is_on` even though `is_sensitive` is `False`"
            )

    async def _call_event_handlers_for_delta_state(
        self, delta_state: JsonDoc
    ) -> None:
        # Trigger on_change event
        try:
            new_value = delta_state["is_on"]
        except KeyError:
            pass
        else:
            assert isinstance(new_value, bool), new_value
            await self.call_event_handler(
                self.on_change,
                CheckboxChangeEvent(new_value),
            )


Checkbox._unique_id_ = "Checkbox-builtin"
