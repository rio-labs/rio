import typing as t

from ..deprecations import deprecated
from ..utils import URL
from .component import Component
from .webview import Webview

__all__ = [
    "Website",
]


@t.final
@deprecated(since="0.10.9", replacement=Webview)
class Website(Component):
    """
    Displays a website.

    `Website` takes a URL as input and displays that website in your app. Since
    the website component cannot know how large its content is going to be,
    you'll probably want to assign a width and height to it.


    ## Attributes
    `url`: The URL of the website you want to display.


    ## Examples

    Here's a simple example that will display an example website:

    ```python
    rio.Website(
        url=rio.URL("https://www.example.com"),
    )
    ```
    """

    url: URL

    def build(self):
        return Webview(self.url)
