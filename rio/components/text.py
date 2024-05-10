from __future__ import annotations

from typing import *  # type: ignore

from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Text",
]


@final
class Text(FundamentalComponent):
    """
    Displays unformatted text.

    `Text` displays text without any formatting, making it one of the most
    commonly used components in Rio.

    While the text itself is unformatted, you can still control the style of
    the text using the `style` attribute. This allows you to change the font
    size, color, and more.


    ## Attributes

    `text`: The text to display.

    `selectable`: Whether the text can be selected by the user.

    `style`: The style of the text. This can either be a `TextStyle` instance,
        or one of the built-in styles: `"heading1"`, `"heading2"`, `"heading3"`,
        `"text"` or `"dim"`.

    `justify`: Controls the alignment of the text within each individual line.


    ## Examples

    A minimal example of a `Text` will be shown:

    ```python
    rio.Text("Hello, world!")
    ```
    """

    text: str
    selectable: bool = True
    style: (
        Literal["heading1", "heading2", "heading3", "text", "dim"]
        | rio.TextStyle
    ) = "text"
    justify: Literal["left", "right", "center", "justify"] = "center"
    wrap: bool | Literal["ellipsize"] = False

    def _custom_serialize(self) -> JsonDoc:
        # Serialization doesn't handle unions. Hence the custom serialization
        # here
        if isinstance(self.style, str):
            style = self.style
        else:
            style = self.style._serialize(self.session)

        return {
            "style": style,
            "wrap": self.wrap,
        }

    def __repr__(self) -> str:
        if len(self.text) > 40:
            text = self.text[:40] + "..."
        else:
            text = self.text

        return f"<{type(self).__name__} id:{self._id} text:{text!r}>"


Text._unique_id = "Text-builtin"
