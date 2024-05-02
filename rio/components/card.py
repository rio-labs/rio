from __future__ import annotations

from dataclasses import KW_ONLY
from typing import *  # type: ignore

from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Card",
]


@final
class Card(FundamentalComponent):
    """
    A container that visually encompasses its child components.

    Cards are used to group related components together, and to visually
    separate them from other components, allowing you to display them in a
    structured way.

    Cards are also often used as large buttons. They can be configured to
    elevate slightly when the mouse hovers over them, indicating to the user
    that they support interaction.


    ## Attributes

    `content`: The component to display inside the card.

    `corner_radius`: The radius of the card's corners. If set to `None`, it
        is picked from the active theme.

    `on_press`: An event handler that is called when the card is clicked.
        Note that attaching an even handler will also modify the appearance
        of the card, to signal the possible interaction to the user. See
        `elevate_on_hover` and `colorize_on_hover` for details.

    `ripple`: Whether the card should display a ripple effect when clicked.
        If set to `None` the card will ripple if an `on_press` event handler is
        attached.

    `elevate_on_hover`: Whether the card should elevate slightly when the
        mouse hovers over it. If set to `None` the card will elevate if
        an `on_press` event handler is attached.

    `colorize_on_hover`: Whether the card should change its color when the
        mouse hovers over it. If set to `None` the card will change its
        color if an `on_press` event handler is attached.

    `color`: The color scheme to use for the card. The color scheme controls
        the background color of the card, and the color of the text and
        icons inside it. Check `rio.Color` for details.


    ## Examples

    This minimal example will simply display a `Card` with the castle icon
    in it:

    ```python
    rio.Card(content=rio.Icon("material/castle"))
    ```

    `Card`s are commonly used to display content. You can easily make your Card
    interactive by adding a lambda function call to on_press:

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            # Create a row with an icon and text
            # as the card content
            card_content = rio.Row(
                rio.Icon(icon="material/castle"),
                rio.Text("Click me!"),
                spacing=1,
                # align the card content in the center
                align_x=0.5,
            )

            return rio.Card(
                content=card_content,
                on_press=lambda: print("Card clicked!"),
                elevate_on_hover=True,
            )
    ```


    You can also use a method for updating the input text and do whatever you
    want. Note that methods are handy if you want to do more than just updating
    the input text. For example run async code or update other components based
    on the input text:

    ```python
    class MyComponent(rio.Component):
        def on_press_card(self) -> None:
            # Do whatever you want when the card is pressed
            print("Card was pressed!")

        def build(self) -> rio.Component:
            # Create a row with an icon and text as the card content
            card_content = rio.Row(
                rio.Icon(icon="material/castle"),
                rio.Text("Click me!"),
                spacing=1,
                # Align the card content in the center
                align_x=0.5,
            )
            return rio.Card(
                content=card_content,
                on_press=self.on_press_card,
                elevate_on_hover=True,
            )
    ```
    """

    content: rio.Component
    _: KW_ONLY
    corner_radius: float | tuple[float, float, float, float] | None = None
    on_press: rio.EventHandler[[]] = None
    ripple: bool | None = None
    elevate_on_hover: bool | None = None
    colorize_on_hover: bool | None = None
    color: rio.ColorSet = "neutral"

    async def _on_message(self, msg: Any) -> None:
        # Trigger the press event
        await self.call_event_handler(self.on_press)

        # Refresh the session
        await self.session._refresh()

    def _custom_serialize(self) -> JsonDoc:
        thm = self.session.theme
        color = thm._serialize_colorset(self.color)

        report_press = self.on_press is not None

        return {
            "corner_radius": (
                thm.corner_radius_medium
                if self.corner_radius is None
                else self.corner_radius
            ),
            "reportPress": report_press,
            "ripple": report_press if self.ripple is None else self.ripple,
            "elevate_on_hover": (
                report_press
                if self.elevate_on_hover is None
                else self.elevate_on_hover
            ),
            "colorize_on_hover": (
                report_press
                if self.colorize_on_hover is None
                else self.colorize_on_hover
            ),
            "color": color,
        }


Card._unique_id = "Card-builtin"
