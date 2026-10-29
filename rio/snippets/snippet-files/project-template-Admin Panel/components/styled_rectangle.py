from __future__ import annotations

import rio


# <component>
class StyledRectangle(rio.Component):
    """
    Styled rectangle component with text and icon. It is used for custom
    dropdowns.

    ## Attributes:

    `text`: The text to display on the rectangle.

    `icon`: The icon to display on the rectangle.

    `on_press`: The event handler to call when the rectangle is pressed.
    """

    text: str
    icon: str | None = None

    on_press: rio.EventHandler[[]] = None

    async def _on_press(self, _: rio.PointerEvent) -> None:
        # Rio has a built-in convenience function for calling event handlers.
        # This function will prevent your code from crashing if something
        # happens in the event handler, and also allows for the handler to be
        await self.call_event_handler(self.on_press)

    def build(self) -> rio.Component:
        # Create a row to hold the icon and text
        content = rio.Row(
            margin=0.5,
            spacing=0.5,
            align_x=0,
        )

        if self.icon is not None:
            content.add(
                rio.Icon(
                    self.icon,
                    align_x=0,
                ),
            )

        content.add(
            rio.Text(
                self.text,
                font_weight="bold",
                font_size=0.9,
                selectable=False,
            ),
        )

        return rio.PointerEventListener(
            rio.Rectangle(
                content=content,
                fill=rio.Color.TRANSPARENT,
                hover_fill=self.session.theme.background_color,
                corner_radius=self.session.theme.corner_radius_small,
                transition_time=0.1,
                cursor="pointer",
            ),
            on_press=self._on_press,
        )


# </component>
