from __future__ import annotations

import pathlib
from dataclasses import KW_ONLY, dataclass
from typing import *  # type: ignore

from uniserde import JsonDoc

import rio

from . import utils
from .fills import FillLike
from .self_serializing import SelfSerializing

__all__ = [
    "Font",
    "TextStyle",
]


class UnsetType:
    pass


UNSET = UnsetType()


@dataclass(frozen=True)
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
    ROBOTO: ClassVar[Font]
    ROBOTO_MONO: ClassVar[Font]


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


@dataclass(frozen=True)
class TextStyle(SelfSerializing):
    """
    A collection of styling properties for text.

    Stores styling information for text - font, size, color, etc.


    ## Attributes

    `font`: The `Font` to use for the text. When set to `None`, the default font
        for the current context (heading or regular text, etc) will be used.

    `fill`: The fill (color, gradient, etc.) for the text.

    `font_size`: The font size.

    `italic`: Whether the text is *italic* or not.

    `font_weight`: Whether the text is normal or **bold**.

    `underlined`: Whether the text is u̲n̲d̲e̲r̲l̲i̲n̲e̲d or not.

    `all_caps`: Whether the text is transformed to ALL CAPS or not.
    """

    _: KW_ONLY
    font: Font | None = None
    fill: FillLike | None = None
    font_size: float = 1.0
    italic: bool = False
    font_weight: Literal["normal", "bold"] = "normal"
    underlined: bool = False
    all_caps: bool = False

    def replace(
        self,
        *,
        font: Font | None = None,
        fill: FillLike | None | UnsetType = UNSET,
        font_size: float | None = None,
        italic: bool | None = None,
        font_weight: Literal["normal", "bold"] | None = None,
        underlined: bool | None = None,
        all_caps: bool | None = None,
    ) -> TextStyle:
        return type(self)(
            font=self.font if font is None else font,
            fill=self.fill if isinstance(fill, UnsetType) else fill,
            font_size=self.font_size if font_size is None else font_size,
            italic=self.italic if italic is None else italic,
            font_weight=self.font_weight
            if font_weight is None
            else font_weight,
            underlined=self.underlined if underlined is None else underlined,
            all_caps=self.all_caps if all_caps is None else all_caps,
        )

    def _serialize(self, sess: rio.Session) -> JsonDoc:
        return {
            "fontName": None
            if self.font is None
            else self.font._serialize(sess),
            "fill": None if self.fill is None else self.fill._serialize(sess),
            "fontSize": self.font_size,
            "italic": self.italic,
            "fontWeight": self.font_weight,
            "underlined": self.underlined,
            "allCaps": self.all_caps,
        }
