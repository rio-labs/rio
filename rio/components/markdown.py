from dataclasses import KW_ONLY
from typing import final

from .fundamental_component import FundamentalComponent

__all__ = [
    "Markdown",
]


@final
class Markdown(FundamentalComponent):
    '''
    Displays Markdown-formatted text.

    Markdown is a lightweight markup language that allows you to write text with
    simple formatting, such as **bold**, *italics*, and links. The `Markdown`
    component displays text formatted with the Markdown syntax.

    Markdown is a great way to write text that is both human-readable, yet
    beautifully formatted.


    ## Attributes

    `text`: The markdown-formatted text to display.

    `default_language`: The default language to use for code blocks. If
        `None`, Rio will try to guess the language automatically. If a
        default is given, it will be used for all code blocks that don't
        specify a language explicitly.

        Inline code will always use the default language, since they are too
        short to reliably guess the language - so make sure to set a default
        language if you want your inline code to be syntax-highlighted.


    ## Examples

    This example will display a short markdown-formatted text:

    ```python
    rio.Markdown(
        """
    # Hello, world!

    I am a **Markdown** component and my job is to display _formatted_ text.
    """
    )
    ```
    '''

    text: str
    _: KW_ONLY
    default_language: str | None = None


Markdown._unique_id = "Markdown-builtin"
