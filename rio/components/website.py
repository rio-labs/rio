from typing import *  # type: ignore

from ..common import URL
from .fundamental_component import FundamentalComponent

__all__ = [
    "Website",
]


class Website(FundamentalComponent):
    """
    # Website

    Displays a website.

    `Website` takes a URL as input and displays that website in your app.

    ## Attributes:

        `url`: The URL of the website you want to display.

    ## Example:

    A minimal example of a `Website` will be shown:

    ```python
    rio.Website(url=rio.URL("https://www.example.com"))
    ```
    """

    url: URL


Website._unique_id = "Website-builtin"
