from typing import final

from ..utils import URL
from .fundamental_component import FundamentalComponent

__all__ = [
    "Website",
]


@final
class Website(FundamentalComponent):
    """
    Displays a website.

    `Website` takes a URL as input and displays that website in your app.


    ## Attributes
    `url`: The URL of the website you want to display.


    ## Examples

    A minimal example of a `Website` will be shown:

    ```python
    rio.Website(url=rio.URL("https://www.example.com"))
    ```
    """

    url: URL


Website._unique_id = "Website-builtin"
