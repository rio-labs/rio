from __future__ import annotations

from dataclasses import KW_ONLY
from typing import *  # type: ignore

import rio

from . import component

__all__ = [
    "Banner",
]


@final
class Banner(component.Component):
    r"""
    Displays a short message to the user.

    Banners can either show a short text message to users, or disappear entirely
    if no message is set. Use them to inform the user about the result of an
    action, to give feedback on their input, or anything else that needs to be
    communicated.

    The messages have one of four styles: `"info"`, `"success"`, `"warning"`,
    and `"danger"`. These control the appearance of the notification bar, and
    allow you to quickly communicate the nature of the message to the user.


    ## Attributes

    `text`: The text to display. If `None` or empty, the banner will disappear
        entirely.

    `style`: Controls the appearance of the banner. The style is one of
        `"info"`, `"success"`, `"warning"` and `"danger"`. Depending on the
        value the banner may change its colors and icon.

    `markdown`: If `True`, the banner text will be rendered as Markdown,
        otherwise it will be rendered as plain text.

    ## Examples

    This shows the most simple usage of a `Banner`:

    ```python
    rio.Banner(
        text="This is a banner",
        style="info",
    )
    ```

    `Banner`s are commonly used to inform the users of about the result of an
    action. You can easily achieve this by adding a banner to a column and
    setting its text when that action completes (or fails!). Here's an example:

    ```python
    class MyComponent(rio.Component):
        banner_text: str = ""

        def on_press_button(self) -> None:
            self.banner_text = "Button pressed!"

        def build(self) -> rio.Component:
            return rio.Column(
                rio.Banner(
                    text=self.banner_text,
                    style="info",
                ),
                rio.Button(
                    content="Press me!",
                    on_press=self.on_press_button,
                ),
                spacing=1,
            )
    ```
    """

    text: str | None
    style: Literal["info", "success", "warning", "danger"]

    _: KW_ONLY
    markdown: bool = False
    icon: str | None = None

    def build(self) -> rio.Component:
        # Early out: Nothing to show
        if self.text is None:
            return rio.Spacer(width=0, height=0)

        text = self.text.strip()
        if not text:
            return rio.Spacer(width=0, height=0)

        # Prepare the style
        if self.style == "info":
            style_name = "secondary"
            icon = "material/info"
        elif self.style == "success":
            style_name = "success"
            icon = "material/check-circle"
        elif self.style == "warning":
            style_name = "warning"
            icon = "material/warning"
        elif self.style == "danger":
            style_name = "danger"
            icon = "material/error"
        else:
            raise ValueError(f"Invalid style: {self.style}")

        if self.icon is not None:
            icon = self.icon

        # Prepare the text child
        if self.markdown:
            text_child = rio.Markdown(
                text,
                width="grow",
            )
        else:
            text_child = rio.Text(
                text,
                width="grow",
                wrap=True,
                justify="left",
            )

        # Build the result
        return rio.Card(
            content=rio.Row(
                rio.Icon(icon),
                text_child,
                spacing=0.5,
                margin=0.5,
            ),
            color=style_name,
            corner_radius=self.session.theme.corner_radius_small,
            elevate_on_hover=False,
        )
