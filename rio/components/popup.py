from __future__ import annotations

import typing as t
from dataclasses import KW_ONLY

from uniserde import JsonDoc

import rio.docs

from .fundamental_component import FundamentalComponent

__all__ = [
    "Popup",
]


@t.final
# @deprecations.component_kwarg_renamed(
#     since="0.9.2",
#     old_name="direction",
#     new_name="position",
# )
class Popup(FundamentalComponent):
    """
    A container which floats above other components.

    Popups are containers which float above the page when open. This allows you
    to keep your app clean by default, but present additional information or
    controls when needed.

    They take two children: The `anchor` is always visible and positions the
    popup. The `content` is located inside the popup and is only visible when
    the popup is open.

    The location popups appear at can be customized using the `direction`,
    `alignment` and `gap` attributes. Popups will do their best to honor those
    settings, but deviate if necessary to ensure they don't go off-screen.


    ## Attributes

    `anchor`: A component which is always visible and positions the popup.

    `content`: A component which is only visible when the popup is open.

    `color`: The color scheme to use for the popup's content. The popup will use the
        specified color as background, while content will automatically use one
        that is legible on top of it.

    `corner_radius`: The radius of the card's corners. If set to `None`, it
        is picked from the active theme.

    `position`: The location at which the popup opens, relative to the anchor.

    `alignment`: The alignment of the popup within the anchor. If the popup
        opens to the left or right, this is the vertical alignment, with `0`
        being the top and `1` being the bottom. If the popup opens to the top or
        bottom, this is the horizontal alignment, with `0` being the left and
        `1` being the right. Has no effect if the popup opens centered.

    `gap`: How much space to leave between the popup and the anchor. Has no
        effect popup opens centered. As all units in Rio, this is measured in
        font-heights.

    `is_open`: Whether the popup is currently open.


    ## Examples

    Most popups are opened by clicking a button. Here's an example that opens and
    closes a popup when a button is pressed:

    ```python
    class MyComponent(rio.Component):
        is_open: bool = False

        def on_button_press(self):
            self.is_open = not self.is_open

        def build(self) -> rio.Component:
            return rio.Popup(
                anchor=rio.Button(
                    "Open Popup",
                    on_press=self.on_button_press,
                ),
                content=rio.Card(
                    content=rio.Text(
                        "Hello World!",
                        justify="center",
                    ),
                    min_width=30,
                    min_height=10,
                ),
                # The popup will open above the anchor
                is_open=self.is_open,
                position="top",
            )
    ```
    """

    # TODO: Add example to docstring

    anchor: rio.Component
    content: rio.Component
    _: KW_ONLY
    color: rio.ColorSet | t.Literal["none"] = "hud"
    corner_radius: float | tuple[float, float, float, float] | None = None
    position: t.Literal[
        "auto", "left", "top", "right", "bottom", "center", "fullscreen"
    ] = "center"
    alignment: float = 0.5
    gap: float = 0.8
    is_open: bool = False

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "color": (
                "none"
                if self.color == "none"
                else self.session.theme._serialize_colorset(self.color)
            ),
            "corner_radius": (
                self.session.theme.corner_radius_medium
                if self.corner_radius is None
                else self.corner_radius
            ),
        }


Popup._unique_id_ = "Popup-builtin"
