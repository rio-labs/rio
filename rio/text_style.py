from __future__ import annotations

import dataclasses
import logging
import pathlib
import typing as t

import cssutils
from uniserde import JsonDoc

import rio

from . import utils
from .assets import Asset, HostedAsset, PathAsset
from .color import Color
from .fills import (
    ImageFill,
    LinearGradientFill,
    RadialGradientFill,
    SolidFill,
)
from .self_serializing import SelfSerializing

__all__ = [
    "Font",
    "TextStyle",
]


# cssutils logs parsing errors. STFU.
logging.getLogger("CSSUTILS").setLevel(logging.CRITICAL)


_TextFill = (
    SolidFill | LinearGradientFill | ImageFill | Color | RadialGradientFill
)


@dataclasses.dataclass(frozen=True)
class FontFace:
    file: HostedAsset
    file_meta: str
    descriptors: dict[str, str]


class Font(SelfSerializing):
    """
    A custom font face.

    The `Font` class lets you create custom fonts for use in your rio app. To
    instantiate a `Font`, you must pass it at least one font file. (As far as
    rio is concerned, the file format is irrelevant - all that matters is that
    a browser can display it.)


    ## Attributes

    `ROBOTO`: A pre-defined font:
        [`Roboto`](https://fonts.google.com/specimen/Roboto).

    `ROBOTO_MONO`: A pre-defined font:
        [`Roboto Mono`](https://fonts.google.com/specimen/Roboto+Mono).
    """

    def __init__(
        self,
        regular: pathlib.Path | bytes,
        bold: pathlib.Path | bytes | None = None,
        italic: pathlib.Path | bytes | None = None,
        bold_italic: pathlib.Path | bytes | None = None,
    ):
        """
        ## Parameters

        `regular`: The regular (i.e. not bold, not italic) font file.

        `bold`: The bold font file.

        `italic`: The italic font file.

        `bold_italic`: The bold and italic font file.
        """
        self._faces = [FontFace(Asset.new(regular), "", {})]

        if bold is not None:
            self._faces.append(
                FontFace(Asset.new(bold), "", {"font-weight": "bold"})
            )

        if italic is not None:
            self._faces.append(
                FontFace(Asset.new(italic), "", {"font-style": "italic"})
            )

        if bold_italic is not None:
            self._faces.append(
                FontFace(
                    Asset.new(bold_italic),
                    "",
                    {"font-weight": "bold", "font-style": "italic"},
                )
            )

        self._google_fonts_name: str | None = None
        self._css_file: pathlib.Path | rio.URL | str | None = None

    @staticmethod
    def from_css_file(css_file: pathlib.Path | rio.URL | str, /) -> Font:
        """
        Loads a font from a CSS file. Any content other than `@font-face`
        declarations is ignored.

        The Rio server will download the font files and rehost them. This means
        clients can use the font even if they don't have an internet connection.

        Note that this method only creates a `Font` object, the CSS is only
        loaded and parsed once your application uses the font. If an error
        occurs during this process, it is printed to stderr.

        ## Parameters

        `css_file`: The CSS file to load. Can be a path, a URL, or a string
            containing the CSS text.
        """
        font = Font(b"")
        font._faces.clear()
        font._css_file = css_file
        return font

    @staticmethod
    def from_google_fonts(font_name: str) -> Font:
        """
        Loads a font from Google Fonts.

        The Rio server will download the font files and rehost them. This means
        clients can use the font even if they don't have an internet connection,
        since they don't need to access Google Fonts themselves.

        Note that this method only creates a `Font` object; the font files are
        only downloaded from Google Fonts once your application uses the font.
        If an error occurs during this process (for example because the font
        name is misspelled), it is printed to stderr.

        ## Parameters

        `font_name`: The name of the font to load. Case-sensitive.
        """

        css_url = rio.URL("https://fonts.googleapis.com/css2").with_query(
            family=font_name
        )
        font = Font.from_css_file(css_url)
        font._google_fonts_name = font_name
        return font

    def _serialize(self, sess: rio.Session) -> str:
        return sess._register_font(self)

    async def _get_faces(self) -> t.AsyncIterable[FontFace]:
        for face in self._faces:
            yield face

        async for face in self._get_faces_from_css_file():
            yield face

    async def _get_faces_from_css_file(self):
        if self._css_file is None:
            return

        # Load the CSS
        if isinstance(self._css_file, str):
            css_text = self._css_file
        else:
            asset = Asset.new(self._css_file, cache_locally=True)
            css_text = await asset.fetch_as_text()

        # Parse it
        font_family: str | None = None

        for rule in cssutils.parseString(css_text):
            if rule.type != rule.FONT_FACE_RULE:
                continue

            src_declarations = list[str]()
            other_descriptors = dict[str, str]()

            for prop in rule.style:
                if prop.name == "font-family":
                    new_font_family = prop.value.strip("'\"")

                    if font_family is None:
                        font_family = new_font_family
                    elif font_family != new_font_family:
                        raise ValueError(
                            f"The CSS contains declarations for multiple different fonts: {font_family!r} and {new_font_family!r}"
                        )
                elif prop.name == "src":
                    src_declarations.append(prop.value)
                else:
                    other_descriptors[prop.name] = prop.value

            for src in src_declarations:
                # The src is actually a comma-separated list of declarations,
                # but cssutils doesn't provide a way to parse each
                # comma-separated declaration individually. We can only parse
                # the whole thing at once, and then we'll have to figure out
                # where the commas were based on the occurrences of `local()`
                # and `uri()`.
                for file, *metadata in utils.group_while(
                    cssutils.css.PropertyValue(src),
                    lambda group, next_value: not isinstance(
                        next_value, cssutils.css.URIValue
                    )
                    and not (
                        isinstance(next_value, cssutils.css.CSSFunction)
                        and next_value.value.startswith("local(")
                    ),
                ):
                    if isinstance(file, cssutils.css.URIValue):
                        yield FontFace(
                            file=Asset.new(
                                rio.URL(file.uri),
                                rehost=True,
                                cache_locally=True,
                            ),
                            file_meta=" ".join(
                                value.cssText for value in metadata
                            ),
                            descriptors=other_descriptors,
                        )

    def __repr__(self) -> str:
        if self._google_fonts_name is not None:
            return f"<Font {self._google_fonts_name!r} from Google Fonts>"
        elif self._css_file is not None:
            return f"<Font {self._css_file!r}>"
        else:
            asset = t.cast(PathAsset, self._faces[0].file)
            return f"<Font {asset.path}>"

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
