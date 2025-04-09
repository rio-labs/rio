from __future__ import annotations

import dataclasses
import typing as t

from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Card",
]


@t.final
class Card(FundamentalComponent):
    """
    A container that visually encompasses its content.

    Cards are used to group related components together, and to visually
    separate them from other components. This is very useful for structuring
    your app and helping users to understand relationships.

    Another common use for cards is as large buttons with custom content. They
    can be configured to elevate slightly when the mouse hovers over them,
    indicating to the user that they support interaction.

    Cards update the theme context for their children, meaning that if you e.g.
    assign the primary color to the card (`color="primary"`), all children will
    automatically switch to a text color that is legible on top of the primary
    color. This means you don't have to worry about colors of components, they
    should always be legible. For this to work correctly prefer to pass colors
    as strings instead of `rio.Color` objects. For example, prefer
    `color="primary"` over `color=self.session.theme.primary_color`. This
    informs Rio about the intent and makes the card automatically switch to the
    "primary" context.

    You can find more details on how theming works in Rio in the [Theming
    Quickstart Guide](https://rio.dev/docs/howto/theming-guide).


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

    `color`: The color scheme to use for the card. The card itself will use the
        specified color, while content will automatically use one that is
        legible on top of it.


    ## Examples

    This minimal example will display a `Card` with the castle icon inside:

    ```python
    rio.Card(content=rio.Icon("material/castle"))
    ```

    `Card`s are commonly used to display content. You can make your Card
    interactive by assigning a function to the `on_press` attribute.

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Card(
                # Add some content to the card
                content=rio.Row(
                    rio.Icon(icon="material/castle"),
                    rio.Text("Click me!"),
                    spacing=1,
                    align_x=0.5,
                ),
                # React to presses
                on_press=lambda: print("Card clicked!"),
                # Signal to the user that the card is interactive. This isn't
                # actually necessary, as the default values is `True` if there
                # is a on_press event handler.
                elevate_on_hover=True,
            )
    ```
    """

    content: rio.Component
    _: dataclasses.KW_ONLY
    corner_radius: float | tuple[float, float, float, float] | None = None
    on_press: rio.EventHandler[[]] = None
    ripple: bool | None = None
    elevate_on_hover: bool | None = None
    colorize_on_hover: bool | None = None
    color: rio.ColorSet = "neutral"

    async def _on_message_(self, msg: t.Any) -> None:
        # Trigger the press event
        await self.call_event_handler(self.on_press)

    def _custom_serialize_(self) -> JsonDoc:
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


Card._unique_id_ = "Card-builtin"
