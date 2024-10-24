import typing as t

from uniserde import JsonDoc

from ..utils import URL
from .fundamental_component import FundamentalComponent

__all__ = [
    "Website",
]


@t.final
class Website(FundamentalComponent):
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

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "url": str(self.url),
        }


Website._unique_id_ = "Website-builtin"
