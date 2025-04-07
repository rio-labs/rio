from __future__ import annotations

import dataclasses
import typing as t

from uniserde import JsonDoc

import rio

from .. import deprecations
from .component import AccessibilityRole, Component, Key
from .fundamental_component import FundamentalComponent

__all__ = ["IconButton"]


@t.final
@deprecations.component_kwarg_renamed(
    since="0.10",
    old_name="size",
    new_name="min_size",
)
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

        - `"major"`: A highly visible button with bold visuals.
        - `"minor"`: A less visible button that doesn't stand out.
        - `"colored-text"`: A minimalistic button with bold text.
        - `"plain-text"`: A button with no background or border. Use this to
          blend less important buttons into the background.

    `color`: The color scheme to use for the button.

    `is_sensitive`: Whether the button should respond to user input.

    `min_size`: The minimum size of the button. This is the width & height of
        the button in font-size units.

    `on_press`: Triggered when the user clicks on the button.

    `accessibility_label`: A short text describing the purpose of the button for
        screen readers. If omitted, the icon name is used.


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
    _: dataclasses.KW_ONLY
    style: t.Literal["major", "minor", "colored-text", "plain-text", "plain"]
    color: rio.ColorSet
    is_sensitive: bool
    min_size: float
    on_press: rio.EventHandler[[]]
    accessibility_label: str | None

    def __init__(
        self,
        icon: str,
        *,
        style: t.Literal[
            "major", "minor", "colored-text", "plain-text", "plain"
        ] = "major",
        color: rio.ColorSet = "keep",
        is_sensitive: bool = True,
        on_press: rio.EventHandler[[]] = None,
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_size: float = 3.7,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] =
        # "never",
        accessibility_label: str | None = None,
        accessibility_role: AccessibilityRole | None = None,
    ) -> None:
        super().__init__(
            key=key,
            margin=margin,
            margin_x=margin_x,
            margin_y=margin_y,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            grow_x=grow_x,
            grow_y=grow_y,
            align_x=align_x,
            align_y=align_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
            accessibility_role=accessibility_role,
        )

        self.icon = icon
        self.min_size = min_size
        self.style = style
        self.color = color
        self.is_sensitive = is_sensitive
        self.on_press = on_press
        self.accessibility_label = accessibility_label

    def build(self) -> rio.Component:
        accessibility_label = self.accessibility_label
        if accessibility_label is None:
            accessibility_label = self.icon.partition("/")[-1]
            accessibility_label = accessibility_label.partition(":")[-1]
            accessibility_label = accessibility_label.replace("_", " ")

        return _IconButtonInternal(
            on_press=self.on_press,
            content=rio.Icon(self.icon, min_width=0, min_height=0),
            style=self.style,
            color=self.color,
            is_sensitive=self.is_sensitive,
            min_width=self.min_size,
            min_height=self.min_size,
            accessibility_label=accessibility_label,
        )

    def _get_debug_details_(self) -> dict[str, t.Any]:
        result = super()._get_debug_details_()

        # `min_width` & `min_height` are replaced with `size`
        del result["min_width"]
        del result["min_height"]

        return result


class _IconButtonInternal(FundamentalComponent):
    content: rio.Component
    style: t.Literal["major", "minor", "colored-text", "plain-text", "plain"]
    color: rio.ColorSet
    is_sensitive: bool
    on_press: rio.EventHandler[[]]
    accessibility_label: str | None
    shape: t.Literal["circle"] = "circle"

    def _custom_serialize_(self) -> JsonDoc:
        if self.style == "plain":
            deprecations.warn(
                since="0.10",
                message=(
                    "The `plain` button style has been renamed to `plain-text`. Please use the new name instead."
                ),
            )

            return {
                "style": "plain-text",
            }

        return {}

    async def _on_message_(self, msg: t.Any) -> None:
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


_IconButtonInternal._unique_id_ = "IconButton-builtin"
