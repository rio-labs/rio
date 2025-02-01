import dataclasses
import typing as t

from uniserde import JsonDoc

from .. import deprecations
from .fundamental_component import FundamentalComponent

__all__ = [
    "Markdown",
]


@t.final
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

    `selectable`: Whether the text can be selected by the user.

    `justify`: Controls the alignment of the text within each individual line.

    `overflow`: What to do with long text. If this is `"nowrap"`, the text will
        be as wide as it needs to be to fit without wrapping. If `"wrap"`, the
        text will wrap to the next line when running out of horizontal space.
        Finally, if `"ellipsize"`, the text will be truncated when there isn't
        enough space and an ellipsis (`...`) will be added.

    `scroll_code_x`: Controls the horizontal scroll behavior of code blocks.
        `"never"` means the code block will always be wide enough to display all
        of its code. In `"auto"` and `"always"` mode, it may shrink and display
        a scroll bar. `"always"` forces the scroll bar to be displayed even when
        it's not needed.

    `scroll_code_y`: Controls the vertical scroll behavior of code blocks.
        `"never"` means the code block will always be wide enough to display all
        of its code. In `"auto"` and `"always"` mode, it may shrink and display
        a scroll bar. `"always"` forces the scroll bar to be displayed even when
        it's not needed.

    `wrap`: Deprecated. Use `overflow` instead.


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
    _: dataclasses.KW_ONLY
    default_language: str | None = None
    selectable: bool = True
    justify: t.Literal["left", "right", "center", "justify"] = "left"
    wrap: bool | t.Literal["ellipsize"] = True
    overflow: t.Literal["nowrap", "wrap", "ellipsize"] = "wrap"
    scroll_code_x: t.Literal["auto", "always", "never"] = "never"
    scroll_code_y: t.Literal["auto", "always", "never"] = "never"

    def _custom_serialize_(self) -> JsonDoc:
        # The old `wrap` attribute has been replaced with `overflow`. Remap the
        # value.
        if self.wrap is not True:
            deprecations.warn_parameter_renamed(
                since="0.10",
                old_name="wrap",
                new_name="overflow",
                function="rio.Markdown",
            )

        if self.wrap is False:
            overflow = "nowrap"
        elif self.wrap == "ellipsize":
            overflow = "ellipsize"
        else:
            overflow = self.overflow

        # Build the result
        return {
            "overflow": overflow,
        }


Markdown._unique_id_ = "Markdown-builtin"
