from __future__ import annotations

from dataclasses import KW_ONLY
from typing import *  # type: ignore

import rio

from .component import Component
from .fundamental_component import FundamentalComponent
from .progress_circle import ProgressCircle

__all__ = ["Button"]


CHILD_MARGIN_X = 1.0
CHILD_MARGIN_Y = 0.3


@final
class Button(Component):
    """
    A clickable button.

    The `Button` component allows the user to trigger an action by clicking on
    it. You can use it to trigger a function call, navigate to a different page,
    or perform any other action you'd like.


    ## Attributes

    `content`: The text or child component to display inside of the button.

    `icon`: The name of an icon to display on the button, in the form
        "set/name:variant". See the `Icon` component for details of how icons
        work in Rio.

    `shape`: The shape of the button. This can be one of:

        - `"pill"`: A rectangle where the left and right sides are completely
            round.
        - `"rounded"`: A rectangle with rounded corners.
        - `"rectangle"`: A rectangle with sharp corners.

    `style`: Controls the button's appearance. This can be one of:

        - `"major"`: A highly visible button with bold visuals.
        - `"minor"`: A less visible button that doesn't stand out.
        - `"plain"`: A button with no background or border. Use this to blend
            unimportant buttons into the background.

    `color`: The color scheme to use for the button.

    `is_sensitive`: Whether the button should respond to user input.

    `is_loading`: Whether the button should display a loading indicator. Use
        this to indicate to the user that an action is currently running.

    `on_press`: Triggered when the user clicks on the button.


    ## Examples

    This code creates a button with the caption "Click me!":

    ```python
    rio.Button(
        "Click me!",
        on_press=lambda: print("Button pressed!"),
    )
    ```

    Icons are an easy way to make your app more visually appealing. Here's a
    button with an icon:

    ```python
    rio.Button(
        "Click me!",
        icon="material/mouse",
        on_press=lambda: print("Button pressed!"),
    )
    ```

    You can even put other components inside of the button. Here's a button with
    a progress bar that slowly fills up as you click it:

    ```python
    class ProgressButton(rio.Component):
        clicks: int = 0

        def _on_button_press(self) -> None:
            self.clicks += 1

        def build(self) -> rio.Component:
            return rio.Button(
                rio.Column(
                    rio.Text("Click repeatedly to fill up the progress bar"),
                    rio.ProgressBar(self.clicks / 10, width=15, height=1),
                ),
                on_press=self._on_button_press,
            )
    ```
    """

    content: str | rio.Component = ""
    _: KW_ONLY
    icon: str | None = None
    shape: Literal["pill", "rounded", "rectangle"] = "pill"
    style: Literal["major", "minor", "plain"] = "major"
    color: rio.ColorSet = "keep"
    is_sensitive: bool = True
    is_loading: bool = False
    on_press: rio.EventHandler[[]] = None

    def build(self) -> rio.Component:
        # Prepare the child
        if self.is_loading:
            child = ProgressCircle(
                size=1.5,
                align_x=0.5,
                margin_x=CHILD_MARGIN_Y,
                margin_y=CHILD_MARGIN_Y,
            )
        elif isinstance(self.content, Component):
            child = rio.Container(
                self.content,
                margin_x=CHILD_MARGIN_Y,
                margin_y=CHILD_MARGIN_Y,
            )
        else:
            children = []
            text = self.content.strip()
            n_children = (self.icon is not None) + bool(text)

            if self.icon is not None:
                children.append(
                    rio.Icon(
                        self.icon,
                        width=1.4,
                        height=1.4,
                        margin_x=CHILD_MARGIN_X if n_children == 1 else None,
                        margin_y=CHILD_MARGIN_Y if n_children == 1 else None,
                        align_x=0.5,
                        align_y=0.5,
                    )
                )

            if text:
                children.append(
                    rio.Text(
                        text,
                        justify="center",
                        margin_x=CHILD_MARGIN_X if n_children == 1 else None,
                        margin_y=CHILD_MARGIN_Y if n_children == 1 else None,
                        style=(
                            rio.TextStyle(font_weight="bold")
                            if self.style == "major"
                            else "text"
                        ),
                        selectable=False,
                    )
                )

            if len(children) == 1:
                child = children[0]
            else:
                child = rio.Row(
                    *children,
                    spacing=0.6,
                    margin_x=CHILD_MARGIN_X,
                    margin_y=CHILD_MARGIN_Y,
                    align_x=0.5,
                )

        # Delegate to a HTML Component
        return _ButtonInternal(
            on_press=self.on_press,
            content=child,
            shape=self.shape,
            style=self.style,
            color=self.color,
            is_sensitive=self.is_sensitive,
            is_loading=self.is_loading,
            width=8 if isinstance(self.content, str) else "natural",
            height=2.2,
        )

    def __str__(self) -> str:
        if isinstance(self.content, str):
            content = f"text:{self.content!r}"
        else:
            content = f"content:{self.content._id}"

        return f"<Button id:{self._id} {content}>"


class _ButtonInternal(FundamentalComponent):
    _: KW_ONLY
    on_press: rio.EventHandler[[]]
    content: rio.Component
    shape: Literal["pill", "rounded", "rectangle", "circle"]
    style: Literal["major", "minor", "plain"]
    color: rio.ColorSet
    is_sensitive: bool
    is_loading: bool

    async def _on_message(self, msg: Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg
        assert msg["type"] == "press", msg

        msg_type: str = msg["type"]
        assert isinstance(msg_type, str), msg_type

        # Is the button sensitive?
        if not self.is_sensitive or self.is_loading:
            return

        # Trigger the press event
        await self.call_event_handler(self.on_press)

        # Refresh the session
        await self.session._refresh()


_ButtonInternal._unique_id = "Button-builtin"
