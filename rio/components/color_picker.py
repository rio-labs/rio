from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import Any, final

from uniserde import JsonDoc

import rio.docs

from .fundamental_component import FundamentalComponent

__all__ = [
    "ColorPicker",
    "ColorChangeEvent",
]


@final
@rio.docs.mark_constructor_as_private
@dataclass
class ColorChangeEvent:
    """
    Holds information regarding a color change event.

    This is a simple dataclass that stores useful information for when the user
    changes a color. You'll typically received this as argument in `on_change`
    events.

    ## Attributes

    `color`: The new `color` of the `ColorPicker`.
    """

    color: rio.Color


@final
class ColorPicker(FundamentalComponent):
    """
    Allows the user to pick a RGB(A) color.

    `ColorPicker` is a component that allows the user to input a color. It
    displays a combination of colorful areas and sliders that the user can
    interact with to pick a color, and optionally an opacity slider to pick
    opacity.


    ## Attributes

    `color`: The color that the user has picked.

    `pick_opacity`: Whether to allow the user to pick opacity. If `False`,
        the opacity slider will be hidden and the color value will be forced
        to be fully opaque.

    `on_change`: This event is triggered whenever the user changes the color.


    ## Examples

    This small example will print a message whenever the user changes the
    selected color:

    ```python
    def print_selected_color(event: rio.ColorChangeEvent):
        print("You selected the color", event.color)

    rio.ColorPicker(
        rio.Color.from_hex("#ff0000"),
        on_change=print_selected_color,
    )
    ```

    This one utilizes a attribute binding to use the selected color as the fill for
    an `Icon`:

    ```python
    class ButtonColorizer(rio.Component):
        color: rio.Color = rio.Color.BLUE

        def build(self) -> rio.Component:
            return rio.Row(
                rio.ColorPicker(
                    color=self.bind().color,
                ),
                rio.Icon(
                    "material/star",
                    fill=self.color,
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
