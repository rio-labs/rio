from .fundamental_component import FundamentalComponent

__all__ = ["Html"]


class Html(FundamentalComponent):
    """
    # Html

    Renders HTML.

    `Html` allows you to embed HTML in your app. It takes HTML code as input and
    renders it. If you want to embed an entire website, use the `Website`
    component instead.


    ## Attributes:

    `html`: The HTML to render.

    ## Example:

    This minimal example will render a simple HTML code:
    TODO: Add example
    """

    html: str


Html._unique_id = "Html-builtin"
