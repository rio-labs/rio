from __future__ import annotations

from dataclasses import KW_ONLY, field
from typing import *  # type: ignore

import rio

from .component import Component

__all__ = [
    "CustomButton",
]


class CustomButton(Component):
    """
    # CustomButton

    A clickable button with customizable visuals.

    Most buttons in apps should fit the main Theme and are well served by the
    `Button` component. However, sometimes you need more control over the
    button's appearance. For example, you might want to create a navigation
    button that integrates well with the rest of the navigation bar.

    For those use cases, the `CustomButton` component is available. It gives you
    full control about the button's appearance, while still providing the
    same functionality as regular buttons.


    ## Attributes:

    `text`: The text to display on the button.

    `is_sensitive`: Whether the button should respond to user input.

    `style_default`: The background style to use when the button is not
            hovered or pressed.

    `style_hover`: The background style to use when the cursor is hovering
            above the button.

    `style_press`: The background style to use when the button is pressed.

    `style_insensitive`: The background style to use when the button is
            not sensitive.

    `text_style_default`: The text style to use when the button is not
            hovered or pressed.

    `text_style_hover`: The text style to use when the cursor is hovering
            above the button.

    `text_style_press`: The text style to use when the button is pressed.

    `text_style_insensitive`: The text style to use when the button is
            not sensitive.

    `transition_speed`: How many seconds it takes for the button to transition
            between styles.

    `ripple`: Whether the button should display a Material Design ripple
            effect when hovered or clicked.

    `on_press`: Triggered when the user clicks on the button.


    ## Example:

    CustomButton enables you to create a button with a fully customized
    appearance. The following example creates a button with a white background
    and black text by default, a black background and white text when hovered, a
    yellow background when pressed, and a magenta background when insensitive.
    The button also transitions between styles:

    ```python
    rio.CustomButton(
        content="Click me!",
        style_default=rio.BoxStyle(
            fill=rio.Color.from_hex("ffffff"),
            corner_radius=1,
        ),
        style_hover=rio.BoxStyle(
            fill=rio.Color.from_hex("000000"),
            corner_radius=2,
        ),
        style_press=rio.BoxStyle(
            fill=rio.Color.from_hex("ffff00"),
        ),
        style_insensitive=rio.BoxStyle(
            fill=rio.Color.from_hex("ff00ff"),
        ),
        text_style_default=rio.TextStyle(),
        text_style_hover=rio.TextStyle(
            fill=rio.Color.from_hex("ffffff"),
        ),
        text_style_press=rio.TextStyle(),
        text_style_insensitive=rio.TextStyle(),
        transition_speed=0.1,
        ripple=True,
    )
    ```
    """

    content: str
    _: KW_ONLY
    is_sensitive: bool = True
    style_default: rio.BoxStyle
    style_hover: rio.BoxStyle
    style_press: rio.BoxStyle
    style_insensitive: rio.BoxStyle
    text_style_default: rio.TextStyle
    text_style_hover: rio.TextStyle
    text_style_press: rio.TextStyle
    text_style_insensitive: rio.TextStyle
    transition_speed: float
    ripple: bool = True
    on_press: rio.EventHandler[[]] = None

    # Internals
    _is_pressed: bool = field(init=False, default=False)
    _is_entered: bool = field(init=False, default=False)

    def _on_mouse_enter(self, event: rio.MouseEnterEvent) -> None:
        self._is_entered = True

    def _on_mouse_leave(self, event: rio.MouseLeaveEvent) -> None:
        self._is_entered = False

    def _on_mouse_down(self, event: rio.MouseDownEvent) -> None:
        # Only react to left mouse button
        if event.button != rio.MouseButton.LEFT:
            return

        self._is_pressed = True

    async def _on_press(self, event: rio.PressEvent) -> None:
        # Only react if sensitive
        if not self.is_sensitive:
            return

        await self.call_event_handler(self.on_press)

        self._is_pressed = False

    def build(self) -> rio.Component:
        # If not sensitive, use the insensitive style
        if not self.is_sensitive:
            style = self.style_insensitive
            text_style = self.text_style_insensitive
            hover_style = None

        # If pressed use the press style
        elif self._is_pressed:
            style = self.style_press
            text_style = self.text_style_press
            hover_style = None

        # Otherwise use the regular styles
        else:
            style = self.style_default
            hover_style = self.style_hover
            text_style = (
                self.text_style_hover if self._is_entered else self.text_style_default
            )

        # Prepare the child
        child = rio.Text(
            self.content,
            selectable=False,  # Make sure the child can be clicked-through
            style=text_style,
            margin=0.3,
        )

        return rio.MouseEventListener(
            rio.Rectangle(
                content=child,
                style=style,
                hover_style=hover_style,
                transition_time=self.transition_speed,
                cursor=(
                    rio.CursorStyle.POINTER
                    if self.is_sensitive
                    else rio.CursorStyle.DEFAULT
                ),
            ),
            on_mouse_enter=self._on_mouse_enter,
            on_mouse_leave=self._on_mouse_leave,
            on_mouse_down=self._on_mouse_down,
            on_press=self._on_press,
        )
