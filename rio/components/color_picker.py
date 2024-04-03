from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import Any

from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "ColorPicker",
    "ColorChangeEvent",
]


@dataclass
class ColorChangeEvent:
    color: rio.Color


class ColorPicker(FundamentalComponent):
    """
    # ColorPicker

    Allows the user to pick an RGB(A) color.

    `ColorPicker` is a component that allows the user to pick a color. It
    displays a combination of colorful areas and sliders that the user can
    interact with to pick a color, and optionally an opacity slider to pick
    opacity.


    ## Attributes:

    `color`: The color that the user has picked.

    `pick_opacity`: Whether to allow the user to pick opacity. If `False`,
            the opacity slider will be hidden and the color value will be forced
            to be fully opaque.

    `on_change`: This event is triggered whenever the user changes the color.


    ## Example:

    This minimal example will simply display a `ColorPicker` with the default
    color red:

    ```python
    rio.ColorPicker(rio.Color.from_hex("#ff0000"))
    ```

    `ColorPicker`s are commonly used to let the user select a color. You can
    easily achieve this by using state bindings to save the color in a variable
    and using it in your application:

    ```python
    class MyComponent(rio.Component):
        color: rio.Color = rio.Color.from_hex("#ff0000")

        def build(self) -> rio.Component:
            return rio.ColorPicker(
                color=self.bind().color,
                pick_opacity=True,
            )
    ```

    If you want to make your `ColorPicker` more interactive, you can easily
    achieve this by adding a lambda function call to on_change:

    ```python
    class MyComponent(rio.Component):
        color: rio.Color = rio.Color.from_hex("#ff0000")

        def build(self) -> rio.Component:
            return rio.ColorPicker(
                color=self.bind().color,
                pick_opacity=True,
                on_change=lambda event: print(f"selected color: {event.color}"),
            )
    ```

    You can use an event handler to react to changes in the color. This example
    will print the color to the console whenever the user changes it:

    ```python
    class MyComponent(rio.Component):
        color: rio.Color = rio.Color.from_rgb(0.5, 0.5, 0.5)

        def on_change_color(self, event: rio.ColorChangeEvent) -> None:
            # You can do whatever you want in this method
            self.color = event.color
            print(f"Selected color: {event.color}")

        def build(self) -> rio.Component:
            return rio.Card(
                rio.ColorPicker(
                    color=self.color,
                    pick_opacity=True,
                    on_change=self.on_change_color,
                ),
            )
    ```
    """

    color: rio.Color
    _: KW_ONLY
    pick_opacity: bool = False
    on_change: rio.EventHandler[ColorChangeEvent] = None

    async def _on_message(self, msg: Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg

        color = rio.Color.from_rgb(*msg["color"])

        # Update the color
        self._apply_delta_state_from_frontend({"color": color})

        # Trigger the change event
        await self.call_event_handler(
            self.on_change,
            ColorChangeEvent(color),
        )

        # Refresh the session
        await self.session._refresh()

    def _custom_serialize(self) -> JsonDoc:
        return {
            "color": self.color.rgba,
        }


ColorPicker._unique_id = "ColorPicker-builtin"
