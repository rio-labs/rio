from __future__ import annotations

import functools
from dataclasses import KW_ONLY, dataclass
from typing import *  # type: ignore

from typing_extensions import Self
from uniserde import Jsonable

import rio

from . import color, common
from . import text_style as text_style_module

__all__ = [
    "Palette",
    "Theme",
]


T = TypeVar("T")


def map_range(value: float, in1: float, in2: float, out1: float, out2: float) -> float:
    """
    Maps a value from one range to another.
    """
    frac = (value - in1) / (in2 - in1)
    frac = min(max(frac, 0), 1)
    return out1 + frac * (out2 - out1)


def color_with_brightness(color: rio.Color, target_brightness: float) -> rio.Color:
    """
    Returns the same shade of color, but with a different brightness. Brightness
    0 corresponds to pure black. 1 is pure white. 0.5 is the original color.
    """
    hue, saturation, value = color.hsv

    # Keep neutral colors neutral
    if saturation == 0 or value == 0:
        return rio.Color.from_grey(
            target_brightness,
            opacity=color.opacity,
        )

    # Otherwise keep the color and adjust the brightness
    return rio.Color.from_hsv(
        hue=hue,
        saturation=map_range(saturation, 0.5, 1, 1, 0),
        value=min(target_brightness * 2, 1),
        opacity=color.opacity,
    )


@dataclass(frozen=True)
class Palette:
    background: rio.Color
    background_variant: rio.Color
    background_active: rio.Color

    foreground: rio.Color

    @classmethod
    def _from_color(
        cls,
        color: rio.Color,
        *,
        colorful: bool,
    ) -> Self:
        # For the foreground color, keep the same shade but adjust the
        # brightness to make it readable.
        current_brightness = color.perceived_brightness

        if colorful:
            brightness_offset = 0.5
            brightness_cutoff = 0.2
        else:
            brightness_offset = 0.8
            brightness_cutoff = 0.08

        target_brightness = (
            current_brightness - brightness_offset
            if current_brightness > 0.55  # Bias towards bright labels
            else current_brightness + brightness_offset
        )
        target_brightness = max(
            min(target_brightness, 1 - brightness_cutoff), brightness_cutoff
        )

        return cls(
            background=color,
            background_variant=color.brighter(0.05),
            background_active=color.brighter(0.15),
            foreground=color_with_brightness(color, target_brightness),
        )

    def replace(
        self,
        background: rio.Color | None = None,
        background_variant: rio.Color | None = None,
        background_active: rio.Color | None = None,
        foreground: rio.Color | None = None,
    ) -> Palette:
        return Palette(
            background=common.first_non_null(background, self.background),
            background_variant=common.first_non_null(
                background_variant, self.background_variant
            ),
            background_active=common.first_non_null(
                background_active, self.background_active
            ),
            foreground=common.first_non_null(foreground, self.foreground),
        )


@dataclass(frozen=True)
class Theme:
    """
    Defines the visual style of the application.

    The `Theme` contains all colors, text styles, and other visual properties
    that are used throughout the application. If you wish to change the
    appearance of your app, this is the place to do it.

    TODO: Finalize theming and document it

    TODO: Give an example for how to create a theme and use it in an app.
    """

    _: KW_ONLY

    primary_palette: Palette
    secondary_palette: Palette

    background_palette: Palette
    neutral_palette: Palette
    hud_palette: Palette
    disabled_palette: Palette

    success_palette: Palette
    warning_palette: Palette
    danger_palette: Palette

    # Other
    corner_radius_small: float
    corner_radius_medium: float
    corner_radius_large: float

    shadow_color: rio.Color

    font: text_style_module.Font
    monospace_font: text_style_module.Font

    # Text styles
    heading1_style: rio.TextStyle
    heading2_style: rio.TextStyle
    heading3_style: rio.TextStyle
    text_style: rio.TextStyle

    @classmethod
    def from_color(
        cls,
        primary_color: rio.Color | None = None,
        secondary_color: rio.Color | None = None,
        background_color: rio.Color | None = None,
        neutral_color: rio.Color | None = None,
        hud_color: rio.Color | None = None,
        disabled_color: rio.Color | None = None,
        success_color: rio.Color | None = None,
        warning_color: rio.Color | None = None,
        danger_color: rio.Color | None = None,
        corner_radius_small: float = 0.5,
        corner_radius_medium: float = 1.4,
        corner_radius_large: float = 2.4,
        color_headings: bool | Literal["auto"] = "auto",
        font: text_style_module.Font = text_style_module.Font.ROBOTO,
        monospace_font: text_style_module.Font = text_style_module.Font.ROBOTO_MONO,
        light: bool = True,
    ) -> Self:
        # Impute defaults
        if primary_color is None:
            primary_color = rio.Color.from_hex("01dffd")

        if secondary_color is None:
            secondary_color = rio.Color.from_hex("0083ff")

        if success_color is None:
            success_color = rio.Color.from_hex("1E8E3E")

        if warning_color is None:
            warning_color = rio.Color.from_hex("F9A825")

        if danger_color is None:
            danger_color = rio.Color.from_hex("B3261E")

        # Extract palettes from the material theme
        primary_palette = Palette._from_color(primary_color, colorful=False)
        secondary_palette = Palette._from_color(secondary_color, colorful=False)

        if light:
            if background_color is None:
                background_palette = Palette(
                    background=rio.Color.WHITE,
                    background_variant=rio.Color.from_grey(0.96).blend(
                        primary_color, 0.04
                    ),
                    background_active=rio.Color.from_grey(0.96).blend(
                        primary_color, 0.1
                    ),
                    foreground=rio.Color.from_grey(0.15),
                )
            else:
                background_palette = Palette._from_color(
                    background_color, colorful=False
                )

            if neutral_color is None:
                neutral_palette = Palette(
                    background=rio.Color.from_grey(0.97).blend(primary_color, 0.04),
                    background_variant=rio.Color.from_grey(0.93).blend(
                        primary_color, 0.07
                    ),
                    background_active=rio.Color.from_grey(0.93).blend(
                        primary_color, 0.15
                    ),
                    foreground=rio.Color.from_grey(0.1),
                )
            else:
                neutral_palette = Palette._from_color(neutral_color, colorful=False)

            if hud_color is None:
                hud_palette = Palette._from_color(
                    rio.Color.from_grey(
                        0.06,
                        opacity=0.9,
                    ),
                    colorful=False,
                )
            else:
                hud_palette = Palette._from_color(hud_color, colorful=False)

            if disabled_color is None:
                disabled_palette = Palette(
                    rio.Color.from_grey(0.7),
                    rio.Color.from_grey(0.75),
                    rio.Color.from_grey(0.80),
                    rio.Color.from_grey(0.4),
                )
            else:
                disabled_palette = Palette._from_color(disabled_color, colorful=False)

            shadow_color = rio.Color.from_rgb(0.1, 0.1, 0.4, 0.3)

        else:
            if background_color is None:
                background_palette = Palette(
                    background=rio.Color.from_grey(0.08).blend(primary_color, 0.02),
                    background_variant=rio.Color.from_grey(0.14).blend(
                        primary_color, 0.04
                    ),
                    background_active=rio.Color.from_grey(0.14).blend(
                        primary_color, 0.10
                    ),
                    foreground=rio.Color.from_grey(0.9),
                )
            else:
                background_palette = Palette._from_color(
                    background_color, colorful=False
                )

            if neutral_color is None:
                neutral_palette = Palette(
                    background=rio.Color.from_grey(0.16).blend(primary_color, 0.03),
                    background_variant=rio.Color.from_grey(0.2).blend(
                        primary_color, 0.04
                    ),
                    background_active=rio.Color.from_grey(0.2).blend(
                        primary_color, 0.10
                    ),
                    foreground=rio.Color.from_grey(0.5),
                )
            else:
                neutral_palette = Palette._from_color(neutral_color, colorful=False)

            if hud_color is None:
                hud_palette = Palette._from_color(
                    rio.Color.from_grey(
                        0.2,
                        opacity=0.8,
                    ),
                    colorful=False,
                )
            else:
                hud_palette = Palette._from_color(hud_color, colorful=False)

            if disabled_color is None:
                disabled_palette = Palette(
                    rio.Color.from_grey(0.2),
                    rio.Color.from_grey(0.15),
                    rio.Color.from_grey(0.10),
                    rio.Color.from_grey(0.6),
                )
            else:
                disabled_palette = Palette._from_color(disabled_color, colorful=False)

            shadow_color = rio.Color.from_rgb(0.0, 0.0, 0.1, 0.35)

        # Semantic colors
        success_palette = Palette._from_color(success_color, colorful=True)
        warning_palette = Palette._from_color(warning_color, colorful=True)
        danger_palette = Palette._from_color(danger_color, colorful=True)

        # Colorful headings can be a problem when the primary color is similar
        # to the background/neutral color. If the `color_headings` argument is
        # set to `auto`, disable coloring if the colors are close.
        if color_headings == "auto":
            brightness1 = primary_palette.background.perceived_brightness
            brightness2 = background_palette.background.perceived_brightness

            color_headings = abs(brightness1 - brightness2) > 0.3

        # Text styles
        text_color = rio.Color.from_grey(0.1 if light else 0.9)

        heading1_style = rio.TextStyle(
            font_size=3.0,
            fill=primary_color if color_headings else text_color,
        )
        heading2_style = heading1_style.replace(font_size=1.8)
        heading3_style = heading1_style.replace(font_size=1.2)
        text_style = heading1_style.replace(
            font_size=1,
            fill=text_color,
        )

        return cls(
            primary_palette=primary_palette,
            secondary_palette=secondary_palette,
            background_palette=background_palette,
            neutral_palette=neutral_palette,
            hud_palette=hud_palette,
            disabled_palette=disabled_palette,
            success_palette=success_palette,
            warning_palette=warning_palette,
            danger_palette=danger_palette,
            corner_radius_small=corner_radius_small,
            corner_radius_medium=corner_radius_medium,
            corner_radius_large=corner_radius_large,
            shadow_color=shadow_color,
            font=font,
            monospace_font=monospace_font,
            heading1_style=heading1_style,
            heading2_style=heading2_style,
            heading3_style=heading3_style,
            text_style=text_style,
        )

    @classmethod
    def pair_from_color(
        cls,
        *,
        primary_color: rio.Color | None = None,
        secondary_color: rio.Color | None = None,
        background_color: rio.Color | None = None,
        neutral_color: rio.Color | None = None,
        hud_color: rio.Color | None = None,
        disabled_color: rio.Color | None = None,
        success_color: rio.Color | None = None,
        warning_color: rio.Color | None = None,
        danger_color: rio.Color | None = None,
        corner_radius_small: float = 0.6,
        corner_radius_medium: float = 1.6,
        corner_radius_large: float = 2.6,
        font: text_style_module.Font = text_style_module.Font.ROBOTO,
        monospace_font: text_style_module.Font = text_style_module.Font.ROBOTO_MONO,
        color_headings: bool | Literal["auto"] = "auto",
    ) -> tuple[Self, Self]:
        func = functools.partial(
            cls.from_color,
            primary_color=primary_color,
            secondary_color=secondary_color,
            background_color=background_color,
            neutral_color=neutral_color,
            hud_color=hud_color,
            disabled_color=disabled_color,
            success_color=success_color,
            warning_color=warning_color,
            danger_color=danger_color,
            corner_radius_small=corner_radius_small,
            corner_radius_medium=corner_radius_medium,
            corner_radius_large=corner_radius_large,
            font=font,
            monospace_font=monospace_font,
            color_headings=color_headings,
        )
        return (
            func(light=True),
            func(light=False),
        )

    def text_color_for(self, color: rio.Color) -> rio.Color:
        """
        Given the color of a background, return which color should be used for
        text on top of it.
        """
        if color.perceived_brightness > 0.6:
            return rio.Color.from_grey(0.1)
        else:
            return rio.Color.from_grey(0.9)

    def _serialize_colorset(self, color: color.ColorSet) -> Jsonable:
        # A colorset more-or-less translates to a switcheroo. Thus, this
        # function needs to provide all information needed to create one.

        # If the color is a string, just pass it through. In this case there is
        # an actual switcheroo which can be used.
        if isinstance(color, str):
            return color

        # TODO: If the color is identical/very similar to a theme color use the
        #       corresponding switcheroo.

        # Otherwise create all the necessary variables to emulate a switcheroo.
        plain_bg = color
        foreground = self.text_color_for(color)

        plain_bg_variant = plain_bg.blend(foreground, 0.15)
        plain_bg_active = plain_bg.blend(foreground, 0.3)

        return {
            "plainBg": color.rgba,
            "plainBgVariant": plain_bg_variant.rgba,
            "plainBgActive": plain_bg_active.rgba,
            "plainFg": foreground.rgba,
            "accentBg": self.secondary_palette.background.rgba,
            "accentFg": self.secondary_palette.foreground.rgba,
        }

    def replace(
        self,
        primary_palette: Palette | None = None,
        secondary_palette: Palette | None = None,
        background_palette: Palette | None = None,
        neutral_palette: Palette | None = None,
        hud_palette: Palette | None = None,
        disabled_palette: Palette | None = None,
        success_palette: Palette | None = None,
        warning_palette: Palette | None = None,
        danger_palette: Palette | None = None,
        corner_radius_small: float | None = None,
        corner_radius_medium: float | None = None,
        corner_radius_large: float | None = None,
        shadow_color: rio.Color | None = None,
        font_family: text_style_module.Font | None = None,
        monospace_font: text_style_module.Font | None = None,
        heading1_style: rio.TextStyle | None = None,
        heading2_style: rio.TextStyle | None = None,
        heading3_style: rio.TextStyle | None = None,
        text_style: rio.TextStyle | None = None,
    ) -> Theme:
        return Theme(
            primary_palette=common.first_non_null(
                primary_palette, self.primary_palette
            ),
            secondary_palette=common.first_non_null(
                secondary_palette, self.secondary_palette
            ),
            background_palette=common.first_non_null(
                background_palette, self.background_palette
            ),
            neutral_palette=common.first_non_null(
                neutral_palette, self.neutral_palette
            ),
            hud_palette=common.first_non_null(hud_palette, self.hud_palette),
            disabled_palette=common.first_non_null(
                disabled_palette, self.disabled_palette
            ),
            success_palette=common.first_non_null(
                success_palette, self.success_palette
            ),
            warning_palette=common.first_non_null(
                warning_palette, self.warning_palette
            ),
            danger_palette=common.first_non_null(danger_palette, self.danger_palette),
            corner_radius_small=common.first_non_null(
                corner_radius_small, self.corner_radius_small
            ),
            corner_radius_medium=common.first_non_null(
                corner_radius_medium, self.corner_radius_medium
            ),
            corner_radius_large=common.first_non_null(
                corner_radius_large, self.corner_radius_large
            ),
            shadow_color=common.first_non_null(shadow_color, self.shadow_color),
            font=common.first_non_null(font_family, self.font),
            monospace_font=common.first_non_null(monospace_font, self.monospace_font),
            heading1_style=common.first_non_null(heading1_style, self.heading1_style),
            heading2_style=common.first_non_null(heading2_style, self.heading2_style),
            heading3_style=common.first_non_null(heading3_style, self.heading3_style),
            text_style=common.first_non_null(text_style, self.text_style),
        )

    @property
    def is_light_theme(self) -> bool:
        return self.primary_palette.background.perceived_brightness >= 0.5

    @property
    def primary_color(self) -> rio.Color:
        return self.primary_palette.background

    @property
    def secondary_color(self) -> rio.Color:
        return self.secondary_palette.background

    @property
    def background_color(self) -> rio.Color:
        return self.background_palette.background

    @property
    def neutral_color(self) -> rio.Color:
        return self.neutral_palette.background

    @property
    def hud_color(self) -> rio.Color:
        return self.hud_palette.background

    @property
    def disabled_color(self) -> rio.Color:
        return self.disabled_palette.background

    @property
    def success_color(self) -> rio.Color:
        return self.success_palette.background

    @property
    def warning_color(self) -> rio.Color:
        return self.warning_palette.background

    @property
    def danger_color(self) -> rio.Color:
        return self.danger_palette.background
