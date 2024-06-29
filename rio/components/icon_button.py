from __future__ import annotations

from dataclasses import KW_ONLY
from typing import *  # type: ignore

import rio

from .component import Component
from .fundamental_component import FundamentalComponent

__all__ = ["IconButton"]


@final
class IconButton(Component):
    """
    # IconButton

    A round, clickable button with an icon.

    The `IconButton` component allows the user to trigger an action by clicking
    on it. You can use it to trigger a function call, navigate to a different
    page, or perform other actions.

    It is similar to the `Button` component, but it is specifically designed to
    display an icon, and it has a round shape.


    ## Attributes

    `icon`: The name of an icon to display on the button, in the form
            `"set/name:variant"`. See the `Icon` component for details of how
            icons work in Rio.

    `style`: Controls the button's appearance. This can be one of:

        - `major`: A highly visible button with bold visuals.
        - `minor`: A less visible button that blends into the background.
        - `plain`: A button with no background or border. Use this to make
                        the button look like a link.

    `color`: The color scheme to use for the button.

    `is_sensitive`: Whether the button should respond to user input.

    `size`: The size of the button. This is the diameter of the button in
            font-size units.

    `on_press`: Triggered when the user clicks on the button.


    ## Examples

    This minimal example will simply display a `IconButton` with a castle icon:

    ```python
    rio.IconButton(icon="material/castle")
    ```

    `IconButton`s are commonly used to trigger actions. You can easily achieve this by
    adding a function call to `on_press`:

    ```python
    class MyComponent(rio.Component):
        def on_press_button(self) -> None:
            print("Icon button pressed!")

        def build(self) -> rio.Component:
            return rio.IconButton(
                icon="material/castle",
                on_press=self.on_press_button,
            )
    ```

    `IconButton`s are commonly used to trigger actions. You can easily achieve
    this by adding a function call to `on_press`. You can use a function call to
    update the banner text signaling that the button was pressed:

    ```python
    class MyComponent(rio.Component):
        banner_text: str = ""

        def on_press_button(self) -> None:
            self.banner_text = "Icon button pressed!"

        def build(self) -> rio.Component:
            return rio.Column(
                rio.Banner(
                    text=self.banner_text,
                    style="info",
                ),
                rio.IconButton(
                    icon="material/castle",
                    on_press=self.on_press_button,
                ),
                spacing=1,
            )
    ```
    """

    icon: str
    _: KW_ONLY
    style: Literal["major", "minor", "plain"]
    color: rio.ColorSet
    is_sensitive: bool
    size: float | Literal["grow"]
    on_press: rio.EventHandler[[]]

    def __init__(
        self,
        icon: str,
        *,
        style: Literal["major", "minor", "plain"] = "major",
        color: rio.ColorSet = "keep",
        is_sensitive: bool = True,
        on_press: rio.EventHandler[[]] = None,
        key: str | int | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        size: float | Literal["grow"] = 3.7,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: Literal["never", "auto", "always"] = "never",
    ):
        super().__init__(
            key=key,
            margin=margin,
            margin_x=margin_x,
            margin_y=margin_y,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            width="natural",
            height="natural",
            align_x=align_x,
            align_y=align_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
        )

        self.icon = icon
        self.size = size
        self.style = style
        self.color = color
        self.is_sensitive = is_sensitive
        self.on_press = on_press

    def build(self) -> rio.Component:
        return _IconButtonInternal(
            on_press=self.on_press,
            content=rio.Icon(self.icon, width=0, height=0),
            style=self.style,
            color=self.color,
            is_sensitive=self.is_sensitive,
            width=self.size,
            height=self.size,
        )

    def _get_debug_details(self) -> dict[str, Any]:
        result = super()._get_debug_details()

        # `width` & `height` are replaced with `size`
        del result["width"]
        del result["height"]

        return result


class _IconButtonInternal(FundamentalComponent):
    content: rio.Component
    style: Literal["major", "minor", "plain"]
    color: rio.ColorSet
    is_sensitive: bool
    on_press: rio.EventHandler[[]]
    shape: Literal["circle"] = "circle"

    async def _on_message(self, msg: Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg
        assert msg["type"] == "press", msg

        msg_type: str = msg["type"]
        assert isinstance(msg_type, str), msg_type

        # Is the button sensitive?
        if not self.is_sensitive:
            return

        # Trigger the press event
        await self.call_event_handler(self.on_press)

        # Refresh the session
        await self.session._refresh()


_IconButtonInternal._unique_id = "IconButton-builtin"
