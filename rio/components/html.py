from typing import final

from .fundamental_component import FundamentalComponent

__all__ = ["Html"]


@final
class Html(FundamentalComponent):
    """
    Renders HTML.

    `Html` allows you to embed HTML in your app. It takes HTML code as input and
    renders it. If you want to embed an entire website, use the `Website`
    component instead.


    ## Attributes

    `html`: The HTML to render.


    ## Examples

    This minimal example will render a simple HTML code:

    ```python
    rio.Html('''
    <h1>Hello World</h1>
    <p>Welcome to rio!</p>
    ''')
    """

    html: str


Html._unique_id = "Html-builtin"
