import typing as t

from .fundamental_component import FundamentalComponent

__all__ = ["Html"]


@t.final
class Html(FundamentalComponent):
    """
    Displays raw HTML.

    The `Html` component allows you to embed arbitrary HTML in your app. It
    takes HTML code as input and renders it.

    To embed an entire website, use the `Website` component instead.


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


Html._unique_id_ = "Html-builtin"
