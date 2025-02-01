import dataclasses
import typing as t

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

    `scroll_code_x`: Controls the horizontal scroll behavior of the displayed
        code. `"never"` means the `CodeBlock` will always be wide enough to
        display all of the code. In `"auto"` and `"always"` mode, it may shrink
        and display a scroll bar. `"always"` forces the scroll bar to be
        displayed even when it's not needed.

    `scroll_code_y`: Controls the vertical scroll behavior of the displayed
        code. `"never"` means the `CodeBlock` will always be tall enough to
        display all of the code. In `"auto"` and `"always"` mode, it may shrink
        and display a scroll bar. `"always"` forces the scroll bar to be
        displayed even when it's not needed.

    ## Examples

    This minimal example will display a `CodeBlock` with the code "pip install
    rio-ui":

    ```python
    rio.CodeBlock("pip install rio-ui", language="bash")
    ```
    """

    code: str

    _: dataclasses.KW_ONLY

    language: str | None = None
    show_controls: bool = True
    scroll_code_x: t.Literal["auto", "always", "never"] = "never"
    scroll_code_y: t.Literal["auto", "always", "never"] = "never"


CodeBlock._unique_id_ = "CodeBlock-builtin"
