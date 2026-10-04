from __future__ import annotations

import dataclasses
import typing as t

from uniserde import JsonDoc

import rio

from ..utils import URL
from .fundamental_component import FundamentalComponent

__all__ = ["Webview"]


@t.final
class Webview(FundamentalComponent):
    """
    Displays a website or renders HTML.

    `Webview` takes a URL or HTML markup as input and displays the website
    or the rendered HTML in your app.

    If the HTML code starts with "<!DOCTYPE " or "<html", it is automatically
    displayed in an iframe.

    Inline JS code can use `rioSendMessage` to send a message to python. On the
    python side, the `Webview`'s `on_message` function will be called with the payload.

    Note that top-level `let`, `const` and `class` declarations are scoped to
    their `<script>` tag and are not shared across tags. (`var` declarations
    and sloppy-mode function declarations are still shared globally.) A
    `'use strict'` directive is honored, but must appear as the first
    statement of the script, optionally preceded by whitespace and `//` /
    `/* */` comments only.


    ## Attributes

    `content`: The URL of the website you want to display, or the HTML
        you want to render.

    `enable_pointer_events`: Whether the `Webview` component (and its contents)
        are clickable.

    `resize_to_fit_content`: Whether the `Webview` component should automatically
        update its size to match the size of its content. Note that this won't
        work if the displayed website's domain doesn't match your own domain.

    `on_message`: Triggered when the HTML content calls
        `rioSendMessage`. The argument is the value passed to the JavaScript
        function.


    ## Examples

    This will display a website based on its URL:

    ```python
    rio.Webview(
        rio.URL("https://www.example.com"),
    )
    ```

    While this will render the given HTML markup:

    ```python
    rio.Webview("<html><body>Hello World</body></html>")
    ```

    The HTML doesn't necessarily have to be an entire website; something
    like this will also work just fine:

    ```python
    rio.Webview("<p>Hello World</p>")
    ```

    This will display a website and handle messages sent from the
    JavaScript `rioSendMessage` function:

    ```python
    class MyComponent(rio.Component):
        message_log: list[str] = []

        def on_message(self, msg: object) -> None:
            self.message_log.append(str(msg))

        def build(self) -> rio.Component:
            return rio.Webview(
                "<script>rioSendMessage('Hello from JS!')</script>",
                on_message=self.on_message,
            )
    ```
    """

    content: URL | str
    _: dataclasses.KW_ONLY
    enable_pointer_events: bool = True
    resize_to_fit_content: bool = True
    on_message: rio.EventHandler[[object]] = None

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "content": str(self.content),
        }

    async def _on_message_(self, msg: t.Any) -> None:
        if self.on_message is not None:
            await self.call_event_handler(self.on_message, msg)


Webview._unique_id_ = "Webview-builtin"
