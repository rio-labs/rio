from dataclasses import KW_ONLY
from typing import final

from .fundamental_component import FundamentalComponent

__all__ = [
    "Markdown",
]


@final
class Markdown(FundamentalComponent):
    """
    Displays Markdown-formatted text.

    `Markdown` displays text formatted using markdown. Markdown is a
    lightweight markup language that allows you to write text with simple
    formatting, such as **bold**, *italics*, and links.

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

    This minimal example will simply display the bold text "Hello World!":

    ```python
    rio.Markdown("**Hello World!**")
    ```
    """

    text: str
    _: KW_ONLY
    default_language: str | None = None


Markdown._unique_id = "Markdown-builtin"
