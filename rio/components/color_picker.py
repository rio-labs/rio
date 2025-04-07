from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings
from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "ColorPicker",
    "ColorChangeEvent",
]


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
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


@t.final
class ColorPicker(FundamentalComponent):
    """
    Allows the user to pick a RGB(A) color.

    `ColorPicker` is a component that allows the user to input a color. It
    displays a combination of colorful areas and sliders that the user can
    interact with to select a color, and optionally also an opacity slider to
    pick opacity.


    ## Attributes

    `color`: The color that the user has picked.

    `pick_opacity`: Whether to allow the user to pick opacity. If `False`,
        the opacity slider will be hidden and the color value will be forced
        to be fully opaque.

    `on_change`: This event is triggered whenever the user changes the color.


    ## Examples

    You can use attribute bindings to access the selected color. Here's an
    example colorizing an icon with the selected color:

    ```python
    class MyComponent(rio.Component):
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

    Alternatively, you can get the selected color by listening for change
    events:

    ```python
    class MyComponent(rio.Component):
        selected_color: rio.Color = rio.Color.from_hex("#ff0000")  # Red

        def print_selected_color(self, event: rio.ColorChangeEvent) -> None:
            self.selected_color = event.color
            print(f"You have selected #{event.color.hexa}")

        def build(self) -> rio.Component:
            return rio.ColorPicker(
                color=self.selected_color,
                on_change=self.print_selected_color,
            )
    ```
    """

    color: rio.Color
    _: dataclasses.KW_ONLY
    pick_opacity: bool = False
    on_change: rio.EventHandler[ColorChangeEvent] = None

    async def _on_message_(self, msg: t.Any) -> None:
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

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "color": self.color.srgba,
        }


ColorPicker._unique_id_ = "ColorPicker-builtin"
