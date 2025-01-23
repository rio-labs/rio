from __future__ import annotations

import colorsys
import typing as t

import typing_extensions as te
from uniserde import Jsonable

import rio

from . import deprecations
from .self_serializing import SelfSerializing

__all__ = [
    "Color",
    "ColorSet",
]


def clamp_1(value: float) -> float:
    """
    Clamp a value to the range [0, 1].
    """
    if value < 0:
        return 0

    if value > 1:
        return 1

    return value


def clamp_05(value: float) -> float:
    """
    Clamp a value to the range [-0.5, 0.5].
    """
    if value < -0.5:
        return -0.5

    if value > 0.5:
        return 0.5

    return value


def _linear_rgb_to_oklab(
    r: float,
    g: float,
    b: float,
) -> tuple[float, float, float]:
    """
    Converts a color from linear sRGB to Oklab. The [original
    source](https://bottosson.github.io/posts/oklab/) is available in the public
    domain as well as the MIT license.
    """

    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

    l_ = l ** (1 / 3)
    m_ = m ** (1 / 3)
    s_ = s ** (1 / 3)

    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def _oklab_to_linear_rgb(
    l: float,
    a: float,
    b: float,
) -> tuple[float, float, float]:
    """
    Converts a color from Oklab to linear sRGB. The [original
    source](https://bottosson.github.io/posts/oklab/) is available in the public
    domain as well as the MIT license.
    """

    l_ = l + 0.3963377774 * a + 0.2158037573 * b
    m_ = l - 0.1055613458 * a - 0.0638541728 * b
    s_ = l - 0.0894841775 * a - 1.2914855480 * b

    l = l_ * l_ * l_
    m = m_ * m_ * m_
    s = s_ * s_ * s_

    # Oklab can represent more colors than plain RGB. Clamping does change the
    # colors somewhat, but ensures valid RGB values.
    return (
        clamp_1(+4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
        clamp_1(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
        clamp_1(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s),
    )


@t.final
class Color(SelfSerializing):
    """
    A color, optionally with an opacity.

    The `Color` class does exactly what it says on the tin: It represents a
    single color. They're used throughout Rio to specify the color of text,
    fills, and more.

    Internally, colors are stored in the
    [Oklab](https://bottosson.github.io/posts/oklab/) color space, a modern
    color space that is designed to be perceptually uniform. Regardless of the
    internal representation, colors can be created from and converted to a
    variety of different color spaces, including linear RGB, sRGB, and HSV.

    ## Examples

    ```python
    # Color from RGB(A)
    Color.from_rgb(1.0, 0.0, 0.0, 1.0)

    # Color from hex
    Color.from_hex("#ff0000")

    # Color from HSV(A)
    Color.from_hsv(0.0, 1.0, 1.0, 1.0)

    # Color from grayscale
    Color.from_gray(0.5, 1.0)

    # Invalid: Don't call `Color` directly
    Color(1.0, 0.0, 0.0, 1.0)  # Raises a `RuntimeError`
    ```

    Regardless of how the color was created, all of the color's components will
    be accessible as attributes. For example, you can access `color.rgb`, even
    if the color was created from HSV values.


    ## Attributes

    `BLACK`: A pure black color.

    `GRAY`: A medium gray color.

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

    _l: float
    _a: float
    _b: float
    _opacity: float

    def __init__(self) -> None:
        """
        ## Metadata

        `public`: False
        """
        raise RuntimeError(
            "Don't call `Color` directly. Use `from_rgb()` and related methods instead."
        )

    @classmethod
    def from_oklab(
        cls,
        l: float,
        a: float,
        b: float,
        opacity: float = 1.0,
    ) -> Color:
        """
        Creates a color from Oklab values.

        Create a color using Oklab values. The `l` and `opacity` values must
        range from `0.0` and `1.0`, inclusive. `a` and `b` range from `-0.5` to
        `0.5`, also inclusive. This is the fastest way to instantiate a new
        `Color`, since colors are internally stored in the Oklab color space.

        ## Parameters

        `l`: The lightness of the color. `0.0` is black, `1.0` is white.

        `a`: The green-red component of the color. `-0.5` is green, `0.5` is
            red.

        `b`: The blue-yellow component of the color. `-0.5` is blue, `0.5` is
            yellow.

        `opacity`: The opacity of the color. `0.0` is fully transparent,
            `1.0` is fully opaque.

        ## Raises

        `ValueError`: If any of the values are outside of their valid ranges.
        """
        # Verify all values
        if l < 0.0 or l > 1.0:
            raise ValueError("`l` must be between 0.0 and 1.0")

        if a < -0.5 or a > 0.5:
            raise ValueError("`a` must be between -0.5 and 0.5")

        if b < -0.5 or b > 0.5:
            raise ValueError("`b` must be between -0.5 and 0.5")

        if opacity < 0.0 or opacity > 1.0:
            raise ValueError("`opacity` must be between 0.0 and 1.0")

        # Instantiate the color, bypassing the blocked constructor.
        self = object.__new__(cls)

        self._l = l
        self._a = a
        self._b = b
        self._opacity = opacity

        return self

    @classmethod
    def from_rgb(
        cls,
        red: float = 1.0,
        green: float = 1.0,
        blue: float = 1.0,
        opacity: float = 1.0,
        srgb: bool = False,
    ) -> Color:
        """
        Creates a color from RGB(A) values.

        Create a color using RGB(A) values. All values must be between `0.0` and
        `1.0`, inclusive.

        If no `opacity` is given, the color will be fully opaque.

        By default, this function assumes the RGB values are in the linear RGB
        color space. To interpret them as sRGB, set the `srgb` parameter to
        `True`.

        ## Parameters

        `red`: The red component of the color. `0.0` is no red, `1.0` is full
            red.

        `green`: The green component of the color. `0.0` is no green, `1.0`
            is full green.

        `blue`: The blue component of the color. `0.0` is no blue, `1.0` is
            full blue.

        `opacity`: The opacity of the color. `0.0` is fully transparent,
            `1.0` is fully opaque.

        `srgb`: Whether the values are in the sRGB color space. If `True`, the
            values will be converted to linear RGB before being stored.

        ## Raises

        `ValueError`: If any of the values are outside of the range `0.0` to
            `1.0`.
        """

        # Sanity check the values
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

        # Make sure the values are linear
        if srgb:
            red = red**2.2
            green = green**2.2
            blue = blue**2.2

        # Instantiate the color
        return Color.from_oklab(
            *_linear_rgb_to_oklab(red, green, blue),
            opacity,
        )

    @classmethod
    def from_hex(
        cls,
        hex_color: str,
        srgb: bool = True,
    ) -> Color:
        """
        Parses a hex string into a color.

        Creates a color parsed from a hex string. A variety of formats are
        supported:

        - `rgb`
        - `rgba`
        - `rrggbb`
        - `rrggbbaa`

        All values may optionally be prefixed with a `#`.

        Note that unlike `from_rgb`, this function assumes the values are in the
        sRGB color space by default, as this is the most common format for hex
        colors. To interpret the values as linear RGB, set the `srgb` parameter
        to `False` instead.

        ## Parameters

        `hex_color`: The hex color string to parse.

        `srgb`: Whether the values are in the sRGB color space. If `True`, the
            values will be converted to linear RGB before being stored.

        ## Raises

        `ValueError`: If the string is not a valid hex color.
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
            srgb=srgb,
        )

    @classmethod
    def from_hsv(
        cls,
        hue: float,
        saturation: float,
        value: float,
        opacity: float = 1.0,
    ) -> Color:
        """
        Create a color from HSV(A) values.

        Create a color using HSV(A) values. All values must be between `0.0` and
        `1.0`, inclusive.

        If no `opacity` is given, the color will be fully opaque.

        ## Parameters

        `hue`: The hue of the color. `0.0` is red, `0.33` is green, `0.66` is
            blue, and `1.0` is red again.

        `saturation`: The saturation of the color. `0.0` is no saturation,
            `1.0` is full saturation.

        `value`: The value of the color. `0.0` is black, `1.0` is full
            brightness.

        `opacity`: The opacity of the color. `0.0` is fully transparent,
            `1.0` is fully opaque.

        ## Raises

        `ValueError`: If any of the values are outside of the range `0.0` to
            `1.0`.
        """
        if hue < 0.0 or hue > 1.0:
            raise ValueError("`hue` must be between 0.0 and 1.0")

        if saturation < 0.0 or saturation > 1.0:
            raise ValueError("`saturation` must be between 0.0 and 1.0")

        if value < 0.0 or value > 1.0:
            raise ValueError("`value` must be between 0.0 and 1.0")

        # The opacity will be checked in the `from_rgb` function, so there's no
        # need to verify it here as well.

        return cls.from_rgb(
            *colorsys.hsv_to_rgb(hue, saturation, value),
            opacity=opacity,
        )

    @classmethod
    @deprecations.deprecated(
        since="0.10.10",
        replacement="Color.from_gray",
    )
    def from_grey(cls, grey: float, opacity: float = 1.0) -> Color:
        """
        Creates a grayscale color.

        Creates a gray color with the given intensity. A `grey` value of 0.0
        corresponds to black, and 1.0 to white.

        If no `opacity` is given, the color will be fully opaque.

        ## Parameters

        `grey`: The intensity of the gray color. `0.0` is black, `1.0` is
            white.

        `opacity`: The opacity of the color. `0.0` is fully transparent,
            `1.0` is fully opaque.

        ## Raises

        `ValueError`: If `grey` is outside of the range `0.0` to `1.0`.
        """
        return cls.from_gray(grey, opacity)

    @classmethod
    def from_gray(cls, gray: float, opacity: float = 1.0) -> Color:
        """
        Creates a grayscale color.

        Creates a gray color with the given intensity. A `gray` value of 0.0
        corresponds to black, and 1.0 to white.

        If no `opacity` is given, the color will be fully opaque.

        ## Parameters

        `gray`: The intensity of the gray color. `0.0` is black, `1.0` is
            white.

        `opacity`: The opacity of the color. `0.0` is fully transparent,
            `1.0` is fully opaque.

        ## Raises

        `ValueError`: If `gray` is outside of the range `0.0` to `1.0`.
        """
        if gray < 0.0 or gray > 1.0:
            raise ValueError("`gray` must be between 0.0 and 1.0")

        # The opacity will be checked in the `from_oklab` function, so there's no
        # need to verify it here as well.

        return cls.from_oklab(
            l=gray,
            a=0.0,
            b=0.0,
            opacity=opacity,
        )

    @property
    def oklab(self) -> tuple[float, float, float]:
        """
        The color as Oklab values.

        The color represented as Oklab values. `l` is in range `0.0` to `1.0`
        inclusive, while `a` and `b` are in the range `-0.5` to `0.5`, also
        inclusive.
        """
        return (self._l, self._a, self._b)

    @property
    def oklaba(self) -> tuple[float, float, float, float]:
        """
        The color as Oklab values, with opacity.

        The color represented as Oklab + opacity values. `l` is in range `0.0`
        to `1.0` inclusive, while `a` and `b` are in the range `-0.5` to `0.5`,
        also inclusive.
        """
        return (self._l, self._a, self._b, self._opacity)

    @property
    def rgb(self) -> tuple[float, float, float]:
        """
        The color as linear RGB values.

        The color represented as RGB values. Each value is between `0.0` and
        `1.0`, inclusive. Note that the values are specifically in linear RGB
        space, not sRGB.
        """
        r, g, b = _oklab_to_linear_rgb(self._l, self._a, self._b)
        return (r, g, b)

    @property
    def rgba(self) -> tuple[float, float, float, float]:
        """
        The color as RGBA values.

        The color represented as RGBA values. Each value is between `0.0` and
        `1.0`, inclusive.
        """
        r, g, b = self.rgb
        return (r, g, b, self._opacity)

    @property
    @deprecations.deprecated(
        since="0.10.10",
        replacement="Color.rgb[0]",
    )
    def red(self) -> float:
        """
        The color's red component.

        The red component of the color. `0.0` is no red, `1.0` is full red. Note
        that this is the linear RGB value, not sRGB.
        """
        return self.rgb[0]

    @property
    @deprecations.deprecated(
        since="0.10.10",
        replacement="Color.rgb[1]",
    )
    def green(self) -> float:
        """
        The color's green component.

        The green component of the color. `0.0` is no green, `1.0` is full
        green. Note that this is the linear RGB value, not sRGB.
        """
        return self.rgb[1]

    @property
    @deprecations.deprecated(
        since="0.10.10",
        replacement="Color.rgb[2]",
    )
    def blue(self) -> float:
        """
        The color's blue component.

        The blue component of the color. `0.0` is no blue, `1.0` is full blue.
        Note that this is the linear RGB value, not sRGB.
        """
        return self.rgb[2]

    @property
    def opacity(self) -> float:
        """
        How opaque the color appears.

        The opacity of the color - also know as the alpha channel. `0.0` is
        fully transparent, `1.0` is fully opaque.
        """
        return self._opacity

    @property
    def srgb(self) -> tuple[float, float, float]:
        """
        The color as sRGB values.

        The color represented as sRGB values. Each value is between `0.0` and
        `1.0`, inclusive. Note that the values are specifically in sRGB space,
        not linear RGB.
        """
        red, green, blue = self.rgb

        return (
            red ** (1 / 2.2),
            green ** (1 / 2.2),
            blue ** (1 / 2.2),
        )

    @property
    def srgba(self) -> tuple[float, float, float, float]:
        """
        The color as sRGBA values.

        The color represented as sRGBA values. Each value is between `0.0` and
        `1.0`, inclusive.
        """
        red, green, blue = self.srgb

        return (
            red,
            green,
            blue,
            self._opacity,
        )

    @property
    def hsv(self) -> tuple[float, float, float]:
        """
        The color as HSV values.

        The color represented as HSV values. Each value is between `0.0` and
        `1.0`, inclusive.
        """
        return colorsys.rgb_to_hsv(*self.rgb)

    @property
    @deprecations.deprecated(
        since="0.10.10",
        replacement="Color.hsv[0]",
    )
    def hue(self) -> float:
        """
        The color's hue.

        The hue of the color, as used in the hsv color model. `0.0` is red,
        `0.33` is green, `0.66` is blue, and `1.0` is red again.
        """
        return self.hsv[0]

    @property
    @deprecations.deprecated(
        since="0.10.10",
        replacement="Color.hsv[1]",
    )
    def saturation(self) -> float:
        """
        The color's saturation.

        The saturation of the color, as used in the hsv color model. `0.0` is no
        saturation, `1.0` is full saturation.
        """
        return self.hsv[1]

    @property
    @deprecations.deprecated(
        since="0.10.10",
        replacement="Color.hsv[2]",
    )
    def value(self) -> float:
        """
        The color's value.

        The value of the color, as used in the hsv color model. `0.0` is black,
        `1.0` is full brightness.
        """
        return self.hsv[2]

    @property
    def perceived_brightness(self) -> float:
        """
        How bright the color appears to humans.

        Approximates how bright the color appears to humans. `0.0` is pitch
        black, `1.0` is as bright as the screen can get.
        """
        return self._l

    @property
    def hex(self) -> str:
        """
        The color as a hex string, without opacity.

        The color, formatted as 6 hex digits. The first two digits are the red
        component, followed by the green component and finally blue. Note that
        the values are in sRGB space, as is common for hex colors.
        """
        red, green, blue = self.srgb

        red_hex = f"{int(round(red*255)):02x}"
        green_hex = f"{int(round(green*255)):02x}"
        blue_hex = f"{int(round(blue*255)):02x}"

        return red_hex + green_hex + blue_hex

    @property
    def hexa(self) -> str:
        """
        The color as a hex string, with opacity.

        The color, formatted as 8 hex digits. The first two digits are the red
        component, followed by the green component, blue, and finally the
        opacity. Note that the values are in sRGB space, as is common for hex
        colors.
        """
        rgb_hex = self.hex
        opacity_hex = f"{int(round(self._opacity*255)):02x}"

        return rgb_hex + opacity_hex

    def replace(
        self,
        *,
        red: float | None = None,
        green: float | None = None,
        blue: float | None = None,
        opacity: float | None = None,
    ) -> Color:
        """
        Replace the given values and return a new `Color` instance.

        Return a new `Color` instance with the given values replaced. Any values
        that are not given will be copied from this color.

        ## Parameters

        `red`: The red component of the new color.

        `green`: The green component of the new color.

        `blue`: The blue component of the new color.

        `opacity`: The opacity of the new color.
        """

        # TODO: What to do with the function parameters? Right now, this
        # function only allows replacing the linear RGB values, but it would be
        # much nicer to also allow replacement of the Oklab values, HSV values,
        # etc.

        cur_red, cur_green, cur_blue = self.rgb

        return Color.from_rgb(
            red=cur_red if red is None else red,
            green=cur_green if green is None else green,
            blue=cur_blue if blue is None else blue,
            opacity=self._opacity if opacity is None else opacity,
        )

    def brighter(self, amount: float) -> Color:
        """
        Return a lighter version of this color.

        Return a new `Color` instance that is brighter than this one by the
        given amount. `0` means no change, `1` will turn the color into white.
        Values less than `0` will darken the color instead.

        The function attempts to keep the hue while making the color appear
        brighter to humans. How exactly this is achieved isn't defined.

        ## Parameters

        `amount`: How much to lighten the color. `0` means no change, `1`
            will turn the color into white. Values less than `0` will
            darken the color instead.


        ## Raises

        `ValueError`: If `amount` is greater than `1`.
        """
        # The amount may be negative. If that is the case, delegate to `darker`
        if amount < 0:
            return self.darker(-amount)

        # Cannot lighten a color beyond white
        if amount > 1:
            raise ValueError("`amount` needs to be less than or equal to 1")

        # From experience, the result looks rather nonlinear. This can be
        # compensated by distorting the amount. There is no particular reason
        # for this value other than that it looks good.
        amount = amount**0.5

        # Not all colors can get equally bright. If we were to just bump the `l`
        # value towards 1 and call it a day, colors would soon go outside of the
        # range supported by RGB (and visible to humans).
        #
        # Find the maximum lightness this shade can have.
        self_hue, self_saturation, _ = self.hsv
        max_l, _, _ = Color.from_hsv(self_hue, self_saturation, 1.0).oklab

        # Interpolate `l` towards 1, making the color brighter
        brighter_l = self._l + (1 - self._l) * amount

        # TODO: This makes the color behave nonlinearly. Account for that?

        # If the resulting color is still below the maximum lightness, the
        # result is good to go.
        if brighter_l <= max_l:
            return Color.from_oklab(
                brighter_l,
                self._a,
                self._b,
                self._opacity,
            )

        # If it wasn't, find out by how much we overshot the mark
        excess = (brighter_l - max_l) / (1 - max_l)
        assert excess > 0, excess

        # Then use that to desaturate the color instead. This, combined with the
        # shift of `l` towards `1` effectively fades towards white.
        scale = 1 - excess

        return Color.from_oklab(
            l=brighter_l,
            a=self._a * scale,
            b=self._b * scale,
            opacity=self._opacity,
        )

    def darker(self, amount: float) -> Color:
        """
        Return a darker version of this color.

        Return a new `Color` instance that is darker than this one by the given
        amount. `0` means no change, `1` will turn the color into black. Values
        less than `0` will brighten the color instead.

        The function attempts to keep the hue while making the color appear
        darker to humans. How exactly this is achieved isn't defined.

        ## Parameters

        `amount`: How much to darken the color. `0` means no change, `1`
            will turn the color into black. Values less than `0` will brighten
            the color instead.

        ## Raises

        `ValueError`: If `amount` is greater than `1`.
        """
        # The value may be negative. If that is the case, delegate to `brighter`
        if amount < 0:
            return self.brighter(-amount)

        # Cannot darken a color beyond black
        if amount > 1:
            raise ValueError("`amount` needs to be less than or equal to 1")

        # HSV has an explicit value for brightness, so convert to HSV and bump
        # the value.
        #
        # The real challenge is avoiding colors from turning black. Changing a
        # 10% gray by `0.1` to black would look like an extreme change to
        # humans, even though being technically correct.
        l, a, b = self.oklab

        # Darkening by `0` should remain the same. Darkening by `1` should turn
        # any color into black. Start off with linear interpolation.
        l = l * (1 - amount)

        # TODO: This makes the color behave nonlinearly. Account for that?

        # Build the result
        return Color.from_oklab(
            l,
            a,
            b,
            self._opacity,
        )

    def desaturated(self, amount: float = 1.0) -> Color:
        """
        Returns a desaturated version of this color.

        Return a copy of this color with the saturation reduced by the given
        amount. `0` means no change, `1` will turn the color into a shade of
        gray.

        ## Parameters

        `amount`: How much to desaturate the color. `0` means no change, `1`
            will turn the color into a shade of gray.


        ## Raises

        `ValueError`: If `amount` is less than `0` or greater than `1`.
        """
        # Make sure the amount is within the valid range
        if amount < 0.0 or amount > 1.0:
            raise ValueError("`amount` must be between 0.0 and 1.0")

        # In Oklab, neutral colors are in the center at `a=0` and `b=0`, meaning
        # the coordinates just need to be scaled down.
        scale = 1 - amount

        return Color.from_oklab(
            l=self._l,
            a=self._a * scale,
            b=self._b * scale,
            opacity=self._opacity,
        )

    def blend(self, other: Color, factor: float) -> Color:
        """
        Blend this color with another color.

        Return a new `Color` instance that is a blend of this color and the
        given `other` color. `factor` controls how much of the other color is
        used. A value of `0` will return this color, a value of `1` will return
        the other color.

        Values outside of the range `0` to `1` are allowed and will lead to the
        color being extrapolated. If the resulting color would have components
        outside of their valid respective ranges, they will be clamped.

        ## Parameters

        `other`: The other color to blend with.

        `factor`: How much of the other color to use. `0` will return this
            color, `1` will return the other color.
        """
        # Plain interpolation as you'd expect. Since extrapolation is also
        # allowed, the values must be clamped to their respective valid ranges.
        one_minus_factor = 1 - factor

        return Color.from_oklab(
            l=clamp_1(
                self._l * one_minus_factor + other._l * factor,
            ),
            a=clamp_05(
                self._a * one_minus_factor + other._a * factor,
            ),
            b=clamp_05(
                self._b * one_minus_factor + other._b * factor,
            ),
            opacity=clamp_1(
                self._opacity * one_minus_factor + other._opacity * factor
            ),
        )

    @property
    def as_plotly(self) -> str:
        """
        The color as a Plotly-compatible string.

        Plotly expects colors to be specified as strings, and this function
        returns the color formatted as such.
        """
        red, green, blue, opacity = self.srgba

        return f"rgba({int(round(red*255))}, {int(round(green*255))}, {int(round(blue*255))}, {opacity})"

    def _serialize(self, sess: rio.Session) -> Jsonable:
        return self.srgba

    def __repr__(self) -> str:
        return f"<Color #{self.hexa}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return NotImplemented

        return self.oklaba == other.oklaba

    def __hash__(self) -> int:
        return hash(self.oklaba)

    # Grays
    BLACK: t.ClassVar[Color]
    GRAY: t.ClassVar[Color]
    WHITE: t.ClassVar[Color]

    # Pure colors
    RED: t.ClassVar[Color]
    GREEN: t.ClassVar[Color]
    BLUE: t.ClassVar[Color]

    # CMY
    CYAN: t.ClassVar[Color]
    MAGENTA: t.ClassVar[Color]
    YELLOW: t.ClassVar[Color]

    # Others
    PINK: t.ClassVar[Color]
    PURPLE: t.ClassVar[Color]
    ORANGE: t.ClassVar[Color]
    BROWN: t.ClassVar[Color]

    # Special
    TRANSPARENT: t.ClassVar[Color]


Color.BLACK = Color.from_rgb(0.0, 0.0, 0.0)
Color.GREY = Color.from_rgb(0.5, 0.5, 0.5)  # type: ignore (Deprecated and thus not annotated)
Color.GRAY = Color.from_rgb(0.5, 0.5, 0.5)
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
ColorSet: te.TypeAlias = (
    Color
    | t.Literal[
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
_color_set_args = set(t.get_args(ColorSet))
