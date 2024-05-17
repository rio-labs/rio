from dataclasses import KW_ONLY
from typing import final

from .fundamental_component import FundamentalComponent

__all__ = [
    "CodeBlock",
]


@final
class CodeBlock(FundamentalComponent):
    """
    Displays source code with syntax highlighting.

    The `CodeBlock` component displays source code with syntax highlighting,
    similar to how it would appear in a code editor, or markdown code block.

    If no language is specified, Rio will try to guess the language
    automatically. To disable syntax highlighting, set the language to `"text"`.

    ## Attributes

    `code`: The markdown-formatted text to display.

    `language`: The default language to use for syntax highlighting. If `None`,
        Rio will try to guess the language automatically. I

    `display_controls`: Whether to display additional controls in addition to the
        source code itself. This includes a button to copy the code to the
        clipboard and a label for the language.
    """

    code: str

    _: KW_ONLY

    language: str | None = None
    display_controls: bool = True


CodeBlock._unique_id = "CodeBlock-builtin"
