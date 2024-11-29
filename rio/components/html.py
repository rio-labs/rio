import dataclasses
import typing as t

from ..deprecations import deprecated
from .component import Component
from .webview import Webview

__all__ = ["Html"]


@t.final
@deprecated(since="0.10.9", replacement=Webview)
class Html(Component):
    """
    Displays raw HTML.

    The `Html` component allows you to embed arbitrary HTML in your app. It
    takes HTML code as input and renders it. If the HTML code starts with
    "<!DOCTYPE " or "<html", it is automatically displayed in an iframe.

    To embed a website based on its URL, use the `Website` component
    instead.


    ## Attributes

    `html`: The HTML to render.

    `enable_pointer_events`: Whether the `Html` component (and its contents)
        are clickable.


    ## Examples

    This minimal example will render a simple HTML code:

    ```python
    rio.Html('''
    <h1>Hello World</h1>
    <p>Welcome to rio!</p>
    ''')
    """

    html: str
    _: dataclasses.KW_ONLY
    enable_pointer_events: bool = True

    def build(self):
        return Webview(
            self.html,
            enable_pointer_events=self.enable_pointer_events,
        )
