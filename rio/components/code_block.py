import typing as t
from dataclasses import KW_ONLY

from .. import deprecations
from .fundamental_component import FundamentalComponent

__all__ = [
    "CodeBlock",
]


@t.final
@deprecations.component_kwarg_renamed(
    since="0.9.2",
    old_name="display_controls",
    new_name="show_controls",
)
class CodeBlock(FundamentalComponent):
    """
    Displays source code with syntax highlighting.

    The `CodeBlock` component displays source code with syntax highlighting,
    similar to how it would appear in a code editor or a markdown code block.

    If no language is specified, Rio will try to guess the language
    automatically. To disable syntax highlighting, set the language to `"text"`.

    ## Attributes

    `code`: The markdown-formatted text to display.

    `language`: The default language to use for syntax highlighting. If `None`,
        Rio will try to guess the language automatically.

    `show_controls`: Whether to display additional controls in addition to the
        source code itself. This includes a button to copy the code to the
        clipboard and a label for the language.

    ## Examples

    This minimal example will display a `CodeBlock` with the code "pip install
    rio-ui":

    ```python
    rio.CodeBlock("pip install rio-ui", language="bash")
    ```
    """

    code: str

    _: KW_ONLY

    language: str | None = None
    show_controls: bool = True


CodeBlock._unique_id_ = "CodeBlock-builtin"
