from __future__ import annotations

import dataclasses
import pathlib
import typing as t

from uniserde import JsonDoc

import rio

from . import utils
from .color import Color
from .fills import ImageFill, LinearGradientFill, SolidFill
from .self_serializing import SelfSerializing

__all__ = [
    "Font",
    "TextStyle",
]


_TextFill = SolidFill | LinearGradientFill | ImageFill | Color


@dataclasses.dataclass(frozen=True)
class Font(SelfSerializing):
    """
    A custom font face.

    The `Font` class lets you create custom fonts for use in your rio app. To
    instantiate a `Font`, you must pass it at least one font file. (As far as
    rio is concerned, the file format is irrelevant - all that matters is that
    a browser can display it.)


    ## Attributes

    `regular`: The regular (i.e. not bold, not italic) font file.

    `bold`: The bold font file.

    `italic`: The italic font file.

    `bold_italic`: The bold and italic font file.

    `ROBOTO`: A pre-defined font:
        [`Roboto`](https://fonts.google.com/specimen/Roboto).

    `ROBOTO_MONO`: A pre-defined font:
        [`Roboto Mono`](https://fonts.google.com/specimen/Roboto+Mono).
    """

    regular: pathlib.Path | bytes
    bold: pathlib.Path | bytes | None = None
    italic: pathlib.Path | bytes | None = None
    bold_italic: pathlib.Path | bytes | None = None

    def _serialize(self, sess: rio.Session) -> str:
        return sess._register_font(self)

    # Predefined fonts
    ROBOTO: t.ClassVar[Font]
    ROBOTO_MONO: t.ClassVar[Font]


Font.ROBOTO = Font(
    regular=utils.RIO_ASSETS_DIR / "fonts/Roboto/Roboto-Regular.ttf",
    bold=utils.RIO_ASSETS_DIR / "fonts/Roboto/Roboto-Bold.ttf",
    italic=utils.RIO_ASSETS_DIR / "fonts/Roboto/Roboto-Italic.ttf",
    bold_italic=utils.RIO_ASSETS_DIR / "fonts/Roboto/Roboto-BoldItalic.ttf",
)

Font.ROBOTO_MONO = Font(
    regular=utils.RIO_ASSETS_DIR / "fonts/Roboto Mono/RobotoMono-Regular.ttf",
    bold=utils.RIO_ASSETS_DIR / "fonts/Roboto Mono/RobotoMono-Bold.ttf",
    italic=utils.RIO_ASSETS_DIR / "fonts/Roboto Mono/RobotoMono-Italic.ttf",
    bold_italic=utils.RIO_ASSETS_DIR
    / "fonts/Roboto Mono/RobotoMono-BoldItalic.ttf",
)


@dataclasses.dataclass(frozen=True)
class TextStyle(SelfSerializing):
    """
    A collection of styling properties for text.

    This is a simple storage class that holds information about how text should
    be styled. You can use it to specify the font, fill, size, and other
    properties of text in your rio app.

    All parameters are optional. Omitting a parameter will leave that setting
    unchanged (i.e. as if you hadn't applied the style at all). For example:

    ```py
    theme = rio.Theme.from_colors(text_color=rio.Color.PURPLE)
    highlighted_style = rio.TextStyle(font_weight="bold", italic=True)

    ...  # Somewhere later

    # This text will be purple, as defined in the theme, but also bold and
    # italic.
    rio.Text("Hello, World!", style=highlighted_style)
    ```


    ## Attributes

    `font`: The `Font` to use for the text.

    `fill`: The fill (color, gradient, etc.) for the text.

    `font_size`: The font size.

    `italic`: Whether the text is *italic* or not.

    `font_weight`: Whether the text is normal or **bold**.

    `underlined`: Whether the text is underlined or not.

    `strikethrough`: Whether the text should have a line through it.

    `all_caps`: Whether the text is transformed to ALL CAPS or not.
    """

    _: dataclasses.KW_ONLY
    font: Font | None = None
    fill: _TextFill | None = None
    font_size: float | None = None
    italic: bool | None = None
    font_weight: t.Literal["normal", "bold"] | None = None
    underlined: bool | None = None
    strikethrough: bool | None = None
    all_caps: bool | None = None

    def replace(
        self,
        *,
        font: Font | None | utils.NotGiven = utils.NOT_GIVEN,
        fill: _TextFill | None | utils.NotGiven = utils.NOT_GIVEN,
        font_size: float | None | utils.NotGiven = utils.NOT_GIVEN,
        italic: bool | None | utils.NotGiven = utils.NOT_GIVEN,
        font_weight: t.Literal["normal", "bold"]
        | None
        | utils.NotGiven = utils.NOT_GIVEN,
        underlined: bool | None | utils.NotGiven = utils.NOT_GIVEN,
        strikethrough: bool | None | utils.NotGiven = utils.NOT_GIVEN,
        all_caps: bool | None | utils.NotGiven = utils.NOT_GIVEN,
    ) -> TextStyle:
        """
        Returns an updated copy of the style.

        This function allows you to create a new `TextStyle` object with the
        same properties as this one, except for the ones you specify.

        ## Parameters

        `font`: The `Font` to use for the text.

        `fill`: The fill (color, gradient, etc.) for the text.

        `font_size`: The font size.

        `italic`: Whether the text is *italic* or not.

        `font_weight`: Whether the text is normal or **bold**.

        `underlined`: Whether the text is underlined or not.

        `strikethrough`: Whether the text should have a line through it.

        `all_caps`: Whether the text is transformed to ALL CAPS or not.
        """
        return TextStyle(
            font=self.font if isinstance(font, utils.NotGiven) else font,
            fill=self.fill if isinstance(fill, utils.NotGiven) else fill,
            font_size=(
                self.font_size
                if isinstance(font_size, utils.NotGiven)
                else font_size
            ),
            italic=(
                self.italic if isinstance(italic, utils.NotGiven) else italic
            ),
            font_weight=(
                self.font_weight
                if isinstance(font_weight, utils.NotGiven)
                else font_weight
            ),
            underlined=(
                self.underlined
                if isinstance(underlined, utils.NotGiven)
                else underlined
            ),
            strikethrough=(
                self.strikethrough
                if isinstance(strikethrough, utils.NotGiven)
                else strikethrough
            ),
            all_caps=(
                self.all_caps
                if isinstance(all_caps, utils.NotGiven)
                else all_caps
            ),
        )

    def _merged_with(self, other: TextStyle) -> TextStyle:
        return TextStyle(
            font=self.font if other.font is None else other.font,
            fill=self.fill if other.fill is None else other.fill,
            font_size=(
                self.font_size if other.font_size is None else other.font_size
            ),
            italic=self.italic if other.italic is None else other.italic,
            font_weight=(
                self.font_weight
                if other.font_weight is None
                else other.font_weight
            ),
            underlined=(
                self.underlined
                if other.underlined is None
                else other.underlined
            ),
            strikethrough=(
                self.strikethrough
                if other.strikethrough is None
                else other.strikethrough
            ),
            all_caps=(
                self.all_caps if other.all_caps is None else other.all_caps
            ),
        )

    def _serialize(self, sess: rio.Session) -> JsonDoc:
        return {
            "fontName": None
            if self.font is None
            else self.font._serialize(sess),
            "fill": sess._serialize_fill(self.fill),
            "fontSize": self.font_size,
            "italic": self.italic,
            "fontWeight": self.font_weight,
            "underlined": self.underlined,
            "strikethrough": self.strikethrough,
            "allCaps": self.all_caps,
        }
