from __future__ import annotations

from dataclasses import KW_ONLY
from typing import *  # type: ignore

import rio

from .component import Component
from .fundamental_component import FundamentalComponent
from .progress_circle import ProgressCircle

__all__ = [
    "Button",
    "IconButton",
]


CHILD_MARGIN_X = 1.0
CHILD_MARGIN_Y = 0.3
INITIALLY_DISABLED_FOR = 0.25


@final
class Button(Component):
    """
    A clickable button.

    The `Button` component allows the user to trigger an action by clicking on
    it. You can use it to trigger a function call, navigate to a different page,
    or perform other actions.


    ## Attributes

    `content`: The text or child component to display inside of the button.

    `icon`: The name of an icon to display on the button, in the form
        "set/name:variant". See the `Icon` component for details of how
        icons work in Rio.

    `shape`: The shape of the button. This can be one of:

        - `"pill"`: A rectangle where the left and right sides are completely
            round.
        - `"rounded"`: A rectangle with rounded corners.
        - `"rectangle"`: A rectangle with sharp corners.

    `style`: Controls the button's appearance. This can be one of:

        - `"major"`: A highly visible button with bold visuals.
        - `"minor"`: A less visible button that blends into the background.
        - `"plain"`: A button with no background or border. Use this to make the
            button look like a link.

    `color`: The color scheme to use for the button.

    `is_sensitive`: Whether the button should respond to user input.

    `is_loading`: Whether the button should display a loading indicator. Use
        this to indicate to the user that an action is currently running.

    `initially_disabled_for`: The number of seconds the button should be
        disabled for after it is first rendered. This is useful to prevent
        the user from accidentally pressing a button that suddenly appeared.

    `on_press`: Triggered when the user clicks on the button.


    ## Examples

    This code creates a button with the caption "Click me!":

    ```python
    rio.Button(
        "Click me!",
        on_press=lambda: print("Button pressed!"),
    )
    ```

    You can make it a little fancier by adding an icon:

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
    initially_disabled_for: float = INITIALLY_DISABLED_FOR
    on_press: rio.EventHandler[[]] = None

    def build(self) -> rio.Component:
        # Prepare the child
        if self.is_loading:
            if self.color in ("keep", "secondary"):
                progress_color = "primary"
            else:
                progress_color = "secondary"

            child = ProgressCircle(
                size=1.5,
                align_x=0.5,
                margin_x=CHILD_MARGIN_Y,
                margin_y=CHILD_MARGIN_Y,
                color=progress_color,
            )
        elif isinstance(self.content, Component):
            child = rio.Container(
                self.content,
                margin_x=CHILD_MARGIN_Y,
                margin_y=CHILD_MARGIN_Y,
                align_x=0.5,
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
                    )
                )

            if text:
                children.append(
                    rio.Text(
                        text,
                        margin_x=CHILD_MARGIN_X if n_children == 1 else None,
                        margin_y=CHILD_MARGIN_Y if n_children == 1 else None,
                        style=(
                            rio.TextStyle(font_weight="bold")
                            if self.style == "major"
                            else "text"
                        ),
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
        has_content = not isinstance(self.content, str) or self.content

        return _ButtonInternal(
            on_press=self.on_press,
            content=child,
            shape=self.shape,
            style=self.style,
            color=self.color,
            is_sensitive=self.is_sensitive,
            is_loading=self.is_loading,
            initially_disabled_for=self.initially_disabled_for,
            width=8 if has_content else 4,
            height=2.2,
        )

    def __str__(self) -> str:
        if isinstance(self.content, str):
            content = f"text:{self.content!r}"
        else:
            content = f"content:{self.content._id}"

        return f"<Button id:{self._id} {content}>"


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

    `initially_disabled_for`: The number of seconds the button should be
            disabled for after it is first rendered. This is useful to prevent
            the user from accidentally triggering an action when the page is
            first loaded.

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
    initially_disabled_for: float = INITIALLY_DISABLED_FOR
    size: float
    on_press: rio.EventHandler[[]]

    def __init__(
        self,
        icon: str,
        *,
        style: Literal["major", "minor", "plain"] = "major",
        color: rio.ColorSet = "keep",
        is_sensitive: bool = True,
        on_press: rio.EventHandler[[]] = None,
        key: str | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        size: float = 3.7,
        align_x: float | None = None,
        align_y: float | None = None,
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
        )

        self.icon = icon
        self.size = size
        self.style = style
        self.color = color
        self.is_sensitive = is_sensitive
        self.on_press = on_press
        self.initially_disabled_for = INITIALLY_DISABLED_FOR

    def build(self) -> rio.Component:
        return _ButtonInternal(
            on_press=self.on_press,
            content=rio.Icon(
                self.icon,
                height=self.size * 0.65,
                width=self.size * 0.65,
                align_x=0.5,
                align_y=0.5,
            ),
            shape="circle",
            style=self.style,
            color=self.color,
            is_sensitive=self.is_sensitive,
            is_loading=False,
            width=self.size,
            height=self.size,
            initially_disabled_for=self.initially_disabled_for,
            # Make sure the button has a square aspect ratio
            align_x=0.5,
            align_y=0.5,
        )

    def _get_debug_details(self) -> dict[str, Any]:
        result = super()._get_debug_details()

        # `width` & `height` are replaced with `size`
        del result["width"]
        del result["height"]

        return result


class _ButtonInternal(FundamentalComponent):
    _: KW_ONLY
    on_press: rio.EventHandler[[]]
    content: rio.Component
    shape: Literal["pill", "rounded", "rectangle", "circle"]
    style: Literal["major", "minor", "plain"]
    color: rio.ColorSet
    is_sensitive: bool
    is_loading: bool
    initially_disabled_for: float

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
