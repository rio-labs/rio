from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import *  # type: ignore

from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Switch",
    "SwitchChangeEvent",
]


@final
@dataclass
class SwitchChangeEvent:
    is_on: bool


@final
class Switch(FundamentalComponent):
    """
    An input for `True` / `False` values.

    Switches allow the user to toggle between an "on" and an "off" state. They
    thus correspond to a Python `bool` value. Use them to allow the user to
    enable or disable certain features, or to select between two options.


    ## Attributes

    `is_on`: Whether the switch is currently in the "on" state.

    `is_sensitive`: Whether the switch should respond to user input.

    `on_change`: Triggered when the user toggles the switch.


    ## Examples

    A minimal example of a `Switch` will be shown:

    ```python
    rio.Switch(is_on=True)
    ```

    You can also bind the value of the switch to a state variable. This will
    update the state variable whenever the switch value changes:

    ```python
    class MyComponent(rio.Component):
        is_on: bool = False

        def build(self) -> rio.Component:
            return rio.Switch(
                is_on=self.bind().is_on,
                on_change=lambda event: print(
                    f"Switch is now {'on' if event.is_on else 'off'}"
                ),
            )
    ```

    You can also listen to changes in the switch by providing an on_change
    callback:

    ```python
    class MyComponent(rio.Component):
        is_on: bool = False

        def on_change(self, event: rio.SwitchChangeEvent):
            self.is_on = event.is_on
            # You can do whatever you here like printing the state
            print(f"Switch is now {'on' if event.is_on else 'off'}")

        def build(self) -> rio.Component:
            return rio.Switch(
                is_on=self.is_on,
                on_change=self.on_change,
            )
    ```
    """

    is_on: bool = False
    _: KW_ONLY
    is_sensitive: bool = True
    on_change: rio.EventHandler[SwitchChangeEvent] = None

    def _validate_delta_state_from_frontend(self, delta_state: JsonDoc) -> None:
        if not set(delta_state) <= {"is_on"}:
            raise AssertionError(
                f"Frontend tried to change `{type(self).__name__}` state: {delta_state}"
            )

        if "is_on" in delta_state and not self.is_sensitive:
            raise AssertionError(
                f"Frontend tried to set `Switch.is_on` even though `is_sensitive` is `False`"
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
                SwitchChangeEvent(new_value),
            )


Switch._unique_id = "Switch-builtin"
