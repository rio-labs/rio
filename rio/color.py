from __future__ import annotations

import colorsys
import math
from typing import *  # type: ignore

from typing_extensions import TypeAlias
from uniserde import Jsonable

import rio

from .self_serializing import SelfSerializing

__all__ = [
    "Color",
    "ColorSet",
]


@final
class Color(SelfSerializing):
    """
    A color, optionally with an opacity.

    The `Color` class does exactly what it says on the tin: It represents a
    single color. They're used throughout Rio to specify the color of text,
    fills, and more.

    `Color` supports a variety of color spaces:

    ```python
    # Color from RGB(A)
    Color.from_rgb(1.0, 0.0, 0.0, 1.0)

    # Color from hex
    Color.from_hex("#ff0000")

    # Color from HSV(A)
    Color.from_hsv(0.0, 1.0, 1.0, 1.0)

    # Color from greyscale
    Color.from_grey(0.5, 1.0)

    # Invalid: Don't call `Color` directly
    Color(1.0, 0.0, 0.0, 1.0)  # Raises a `RuntimeError`
    ```

    Regardless of how the color was created, all of the color's components will
    be accessible as attributes. For example, you can access `color.red`, even
    if the color was created from HSV values.


    ## Attributes

    `BLACK`: A pure black color.

    `GREY`: A medium grey color.

    `WHITE`: A pure white color.

    `RED`: A pure red color.

    `GREEN`: A pure green color.

    `BLUE`: A pure blue color.

    `CYAN`: A pure cyan color.

    `MAGENTA`: A pure magenta color.

    `YELLOW`: A pure yellow color.

    `PINK`: A pure pink color.

    `PURPLE`: A pure purple color.

    `ORANGE`: A pure orange color.

    `BROWN`: A pure brown color.

    `TRANSPARENT`: A fully transparent color.
    """

    _red: float
    _green: float
    _blue: float
    _opacity: float

    def __init__(self):
        """
        ## Metadata

        public: False
        """
        raise RuntimeError(
            "Don't call `Color` directly. Use `from_rgb()` and related methods instead."
        )

    @classmethod
    def from_rgb(
        cls,
        red: float = 1.0,
        green: float = 1.0,
        blue: float = 1.0,
        opacity: float = 1.0,
    ) -> "Color":
        """
        Creates a color from RGB(A) values.

        Creates a color from RGB(A) values. All values must be between `0.0` and
        `1.0`, inclusive.

        If no `opacity` is given, the color will be fully opaque.

        ## Parameters

        red: The red component of the color. `0.0` is no red, `1.0` is full
            red.

        green: The green component of the color. `0.0` is no green, `1.0`
            is full green.

        blue: The blue component of the color. `0.0` is no blue, `1.0` is
            full blue.

        opacity: The opacity of the color. `0.0` is fully transparent,
            `1.0` is fully opaque.

        ## Raises

        ValueError: If any of the values are outside of the range `0.0` to
            `1.0`.
        """

        if red < 0.0 or red > 1.0:
            raise ValueError(f"`red` must be between 0.0 and 1.0, not {red}")

        if green < 0.0 or green > 1.0:
            raise ValueError(
                f"`green` must be between 0.0 and 1.0, not {green}"
            )

        if blue < 0.0 or blue > 1.0:
            raise ValueError(f"`blue` must be between 0.0 and 1.0, not {blue}")

        if opacity < 0.0 or opacity > 1.0:
            raise ValueError(
                f"`opacity` must be between 0.0 and 1.0, not {opacity}"
            )

        self = object.__new__(cls)

        self._red = red
        self._green = green
        self._blue = blue
        self._opacity = opacity

        return self

    @classmethod
    def from_hex(cls, hex_color: str) -> "Color":
        """
        Parses a hex string into a color.

        Parses a hex string into a color. A variety of formats are supported:

        - `rgb`
        - `rgba`
        - `rrggbb`
        - `rrggbbaa`

        All values may optionally be prefixed with a `#`.

        ## Raises

        ValueError: If the string is not a valid hex color.
        """
        # Drop any leading `#` if present
        hex_color = hex_color.removeprefix("#")

        # Make sure the string is the correct length
        if len(hex_color) not in (3, 4, 6, 8):
            raise ValueError(
                "The hex string must be 3, 4, 6 or 8 characters long"
            )

        # Split the string into the individual components
        if len(hex_color) == 3:
            rh, gh, bh = hex_color
            ah = "f"
            max = 15
        elif len(hex_color) == 4:
            rh, gh, bh, ah = hex_color
            max = 15
        elif len(hex_color) == 6:
            rh, gh, bh = hex_color[0:2], hex_color[2:4], hex_color[4:6]
            ah = "ff"
            max = 255
        else:
            rh, gh, bh, ah = (
                hex_color[0:2],
                hex_color[2:4],
                hex_color[4:6],
                hex_color[6:8],
            )
            max = 255

        # Parse it
        return cls.from_rgb(
            red=int(rh, 16) / max,
            green=int(gh, 16) / max,
            blue=int(bh, 16) / max,
            opacity=int(ah, 16) / max,
        )

    @classmethod
    def from_hsv(
        cls,
        hue: float,
        saturation: float,
        value: float,
        opacity: float = 1.0,
    ) -> "Color":
        """
        Create a color from HSV(A) values.

        Creates a color from HSV(A) values. All values must be between `0.0` and
        `1.0`, inclusive.

        If no `opacity` is given, the color will be fully opaque.

        ## Parameters

        hue: The hue of the color. `0.0` is red, `0.33` is green, `0.66` is
            blue, and `1.0` is red again.

        saturation: The saturation of the color. `0.0` is no saturation,
            `1.0` is full saturation.

        value: The value of the color. `0.0` is black, `1.0` is full
            brightness.

        opacity: The opacity of the color. `0.0` is fully transparent,
            `1.0` is fully opaque.

        ## Raises

        ValueError: If any of the values are outside of the range `0.0` to
            `1.0`.
        """
        if hue < 0.0 or hue > 1.0:
            raise ValueError("`hue` must be between 0.0 and 1.0")

        if saturation < 0.0 or saturation > 1.0:
            raise ValueError("`saturation` must be between 0.0 and 1.0")

        if value < 0.0 or value > 1.0:
            raise ValueError("`value` must be between 0.0 and 1.0")

        # Opacity will be checked by `from_rgb`

        return cls.from_rgb(
            *colorsys.hsv_to_rgb(hue, saturation, value),
            opacity=opacity,
        )

    @classmethod
    def from_grey(cls, grey: float, opacity: float = 1.0) -> "Color":
        """
        Creates a greyscale color.

        Creates a grey color with the given intensity. A `grey` value of 0.0
        corresponds to black, and 1.0 to white.

        If no `opacity` is given, the color will be fully opaque.

        ## Parameters

        grey: The intensity of the grey color. `0.0` is black, `1.0` is
            white.

        opacity: The opacity of the color. `0.0` is fully transparent,
            `1.0` is fully opaque.

        ## Raises

        ValueError: If `grey` is outside of the range `0.0` to `1.0`.
        """
        if grey < 0.0 or grey > 1.0:
            raise ValueError("`grey` must be between 0.0 and 1.0")

        # Opacity will be checked by `from_rgb`

        return cls.from_rgb(grey, grey, grey, opacity)

    @classmethod
    def _from_material_argb(cls, argb: int) -> "Color":
        """
        Creates a new color from the argb value, as used by the
        `material-color-utilities-python` package.
        """

        return cls.from_rgb(
            red=((argb >> 16) & 0xFF) / 255,
            green=((argb >> 8) & 0xFF) / 255,
            blue=(argb & 0xFF) / 255,
            opacity=((argb >> 24) & 0xFF) / 255,
        )

    @property
    def _as_material_argb(self) -> int:
        """
        Returns the argb value, as used by the `material-color-utilities-python`
        package.
        """

        return (
            int(round(self.opacity * 255)) << 24
            | int(round(self.red * 255)) << 16
            | int(round(self.green * 255)) << 8
            | int(round(self.blue * 255))
        )

    @property
    def red(self) -> float:
        """
        The red component of the color.

        The red component of the color. `0.0` is no red, `1.0` is full red.
        """
        return self._red

    @property
    def green(self) -> float:
        """
        The green component of the color.

        The green component of the color. `0.0` is no green, `1.0` is full
        green.
        """
        return self._green

    @property
    def blue(self) -> float:
        """
        The blue component of the color.

        The blue component of the color. `0.0` is no blue, `1.0` is full blue.
        """
        return self._blue

    @property
    def opacity(self) -> float:
        """
        How opaque the color appears.

        The opacity of the color. `0.0` is fully transparent, `1.0` is fully
        opaque.
        """
        return self._opacity

    @property
    def rgb(self) -> tuple[float, float, float]:
        """
        The color as RGB values.

        The color as RGB values. Each value is between `0.0` and `1.0`,
        inclusive.
        """
        return (self._red, self._green, self._blue)

    @property
    def rgba(self) -> tuple[float, float, float, float]:
        """
        The color as RGBA values.

        The color as RGBA values. Each value is between `0.0` and `1.0`,
        inclusive.
        """
        return (self._red, self._green, self._blue, self._opacity)

    @property
    def hsv(self) -> tuple[float, float, float]:
        """
        The color as HSV values.

        The color as HSV values. Each value is between `0.0` and `1.0`,
        inclusive.
        """
        return colorsys.rgb_to_hsv(self._red, self._green, self._blue)

    @property
    def hue(self) -> float:
        """
        The hue of the color.

        The hue of the color. `0.0` is red, `0.33` is green, `0.66` is blue, and
        `1.0` is red again.
        """
        return self.hsv[0]

    @property
    def saturation(self) -> float:
        """
        The saturation of the color.

        The saturation of the color. `0.0` is no saturation, `1.0` is full
        saturation.
        """
        return self.hsv[1]

    @property
    def value(self) -> float:
        """
        The value of the color.

        The value of the color. `0.0` is black, `1.0` is full brightness.
        """
        return self.hsv[2]

    @property
    def perceived_brightness(self) -> float:
        """
        How bright the color appears to humans.

        Approximates how bright the color appears to humans. `0.0` is black,
        `1.0` is full brightness.
        """

        return math.sqrt(
            0.299 * self.red**2 + 0.587 * self.green**2 + 0.114 * self.blue**2
        )

    @property
    def hex(self) -> str:
        """
        The color as a hex string.

        The color, formatted as 8 hex digits. The first two digits are the red
        component, followed by the green component, blue and opacity.
        """

        red_hex = f"{int(round(self.red*255)):02x}"
        green_hex = f"{int(round(self.green*255)):02x}"
        blue_hex = f"{int(round(self.blue*255)):02x}"
        opacity_hex = f"{int(round(self.opacity*255)):02x}"
        return red_hex + green_hex + blue_hex + opacity_hex

    def replace(
        self,
        *,
        red: float | None = None,
        green: float | None = None,
        blue: float | None = None,
        opacity: float | None = None,
    ) -> "Color":
        """
        Return a new `Color` instance with the given values replaced.

        Return a new `Color` instance with the given values replaced. Any values
        that are not given will be copied from this color.

        ## Parameters

        `red`: The red component of the new color.

        `green`: The green component of the new color.

        `blue`: The blue component of the new color.

        `opacity`: The opacity of the new color.
        """

        return Color.from_rgb(
            red=self.red if red is None else red,
            green=self.green if green is None else green,
            blue=self.blue if blue is None else blue,
            opacity=self.opacity if opacity is None else opacity,
        )

    def _map_rgb(self, func: Callable[[float], float]) -> "Color":
        """
        Apply a function to each of the RGB values of this color, and return a
        new `Color` instance with the result. The opacity value is copied
        unchanged.
        """
        return Color.from_rgb(
            func(self.red),
            func(self.green),
            func(self.blue),
            self.opacity,
        )

    def brighter(self, amount: float) -> "Color":
        """
        Return a lighter version of this color.

        Return a new `Color` instance that is brighter than this one by the
        given amount. `0` means no change, `1` will turn the color into white.
        Values less than `0` will darken the color instead.

        How exactly the lightening/darkening happens isn't defined.

        ## Parameters

        amount: How much to lighten the color. `0` means no change, `1`
            will turn the color into white. Values less than `0` will
            darken the color instead.
        """
        # The amount may be negative. If that is the case, delegate to `darker`
        if amount <= 0:
            return self.darker(-amount)

        # HSV has an explicit value for brightness, so convert to HSV and bump
        # the value.
        #
        # Brightening by `1` is supposed to yield white, but because this
        # function starts shifting colors to white after they exceed `1.0` an
        # amount of `2` might be needed to actually get white.
        #
        # -> Apply double the amount
        hue, saturation, value = self.hsv
        value += amount * 2

        # Bumping it might put the value above 1.0. Clip it and see by how much
        # 1.0 was overshot
        value_clip = max(min(value, 1.0), 0.0)
        overshoot = value - value_clip

        # If there was an overshoot, reduce the saturation, thus pushing the
        # color towards white
        saturation = max(saturation - overshoot * 1.0, 0.0)

        return Color.from_hsv(hue, saturation, value_clip)

    def darker(self, amount: float) -> "Color":
        """
        Return a darker version of this color.

        Return a new `Color` instance that is darker than this one by the given
        amount. `0` means no change, `1` will turn the color into black. Values
        less than `0` will brighten the color instead.

        How exactly the lightening/darkening happens isn't defined.

        ## Parameters

        amount: How much to darken the color. `0` means no change, `1`
            will turn the color into black. Values less than `0` will brighten
            the color instead.
        """
        # The value may be negative. If that is the case, delegate to `brighter`
        if amount <= 0:
            return self.brighter(-amount)

        return Color._map_rgb(self, lambda x: max(x - amount, 0))

    def desaturated(self, amount: float) -> "Color":
        """
        Returns a desaturated version of this color.

        Return a copy of this color with the saturation reduced by the given
        amount. `0` means no change, `1` will turn the color into a shade of
        grey.

        ## Parameters

        amount: How much to desaturate the color. `0` means no change, `1`
            will turn the color into a shade of grey.
        """

        if amount < 0.0 or amount > 1.0:
            raise ValueError("`amount` must be between 0.0 and 1.0")

        hue, saturation, brightness = self.hsv
        saturation = saturation * (1 - amount)

        return Color.from_hsv(hue, saturation, brightness)

    def blend(self, other: Color, factor: float) -> Color:
        """
        Blend this color with another color.

        Return a new `Color` instance that is a blend of this color and the
        given `other` color. `factor` controls how much of the other color is
        used. A value of `0` will return this color, a value of `1` will return
        the other color.

        Values outside of the range `0` to `1` are allowed and will lead to the
        color being extrapolated.

        ## Parameters

        other: The other color to blend with.

        factor: How much of the other color to use. `0` will return this
            color, `1` will return the other color.
        """
        one_minus_factor = 1 - factor

        return Color.from_rgb(
            red=self.red * one_minus_factor + other.red * factor,
            green=self.green * one_minus_factor + other.green * factor,
            blue=self.blue * one_minus_factor + other.blue * factor,
            opacity=self.opacity * one_minus_factor + other.opacity * factor,
        )

    @property
    def as_plotly(self) -> str:
        """
        The color as a Plotly-compatible string.

        Plotly expects colors to be specified as strings, and this function
        returns the color formatted as such.
        """
        return f"rgba({int(round(self.red*255))}, {int(round(self.green*255))}, {int(round(self.blue*255))}, {self.opacity})"

    def _serialize(self, sess: rio.Session) -> Jsonable:
        return self.rgba

    def __repr__(self) -> str:
        return f"<Color {self.hex}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return NotImplemented

        return self.rgba == other.rgba

    def __hash__(self) -> int:
        return hash(self.rgba)

    # Greys
    BLACK: ClassVar["Color"]
    GREY: ClassVar["Color"]
    WHITE: ClassVar["Color"]

    # Pure colors
    RED: ClassVar["Color"]
    GREEN: ClassVar["Color"]
    BLUE: ClassVar["Color"]

    # CMY
    CYAN: ClassVar["Color"]
    MAGENTA: ClassVar["Color"]
    YELLOW: ClassVar["Color"]

    # Others
    PINK: ClassVar["Color"]
    PURPLE: ClassVar["Color"]
    ORANGE: ClassVar["Color"]
    BROWN: ClassVar["Color"]

    # Special
    TRANSPARENT: ClassVar["Color"]


Color.BLACK = Color.from_rgb(0.0, 0.0, 0.0)
Color.GREY = Color.from_rgb(0.5, 0.5, 0.5)
Color.WHITE = Color.from_rgb(1.0, 1.0, 1.0)

Color.RED = Color.from_rgb(1.0, 0.0, 0.0)
Color.GREEN = Color.from_rgb(0.0, 1.0, 0.0)
Color.BLUE = Color.from_rgb(0.0, 0.0, 1.0)

Color.CYAN = Color.from_rgb(0.0, 1.0, 1.0)
Color.MAGENTA = Color.from_rgb(1.0, 0.0, 1.0)
Color.YELLOW = Color.from_rgb(1.0, 1.0, 0.0)

Color.PINK = Color.from_rgb(1.0, 0.0, 1.0)
Color.PURPLE = Color.from_rgb(0.5, 0.0, 0.5)
Color.ORANGE = Color.from_rgb(1.0, 0.5, 0.0)

Color.TRANSPARENT = Color.from_rgb(0.0, 0.0, 0.0, 0.0)


# Like color, but also allows referencing theme colors
ColorSet: TypeAlias = (
    Color
    | Literal[
        "background",
        "neutral",
        "hud",
        "primary",
        "secondary",
        "success",
        "warning",
        "danger",
        "keep",
    ]
)


# Cache so the session can quickly determine whether a type annotation is
# `ColorSet`
_color_set_args = set(get_args(ColorSet))
