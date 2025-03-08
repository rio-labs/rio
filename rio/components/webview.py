import dataclasses
import typing as t

from uniserde import JsonDoc

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


    ## Attributes

    `content`: The URL of the website you want to display, or the HTML
        you want to render.

    `enable_pointer_events`: Whether the `Webview` component (and its contents)
        are clickable.

    `resize_to_fit_content`: Whether the `Webview` component should automatically
        update its size to match the size of its content. Note that this won't
        work if the displayed website's domain doesn't match your own domain.


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
    """

    content: URL | str
    _: dataclasses.KW_ONLY
    enable_pointer_events: bool = True
    resize_to_fit_content: bool = True

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "content": str(self.content),
        }


Webview._unique_id_ = "Webview-builtin"
