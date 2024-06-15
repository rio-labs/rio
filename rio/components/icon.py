from __future__ import annotations

from dataclasses import KW_ONLY
from pathlib import Path
from typing import Literal, Union, final

from uniserde import JsonDoc

from .. import color, deprecations, fills, icons
from .fundamental_component import FundamentalComponent

__all__ = [
    "Icon",
]


_IconFill = Union[
    "fills.SolidFill",
    "fills.LinearGradientFill",
    "fills.ImageFill",
    "color.ColorSet",
    Literal["dim"],
]


@final
class Icon(FundamentalComponent):
    """
    Displays one of many pre-bundled icons.

    Icons are a great way to add polish to your app. A good icon can help your
    users understand your app and immediately recognize what a component does.

    Rio includes hundreds of free icons, allowing you to easily add them to your
    app without having to find or create your own. The `Icon` component displays
    one of these icons.

    Note that unlike most components in Rio, the `Icon` component does not have
    a `natural` size, since icons can be easily be scaled to fit any space.
    Because of this, `Icon` defaults to a width and height of 1.3, which is a
    great size when mixing icons with text.

    Icon names are in the format `set-name/icon-name:variant`. Rio already ships
    with the `material` icon set, which contains icons in the style of Google's
    Material Design. You can browse all available icons in Rio's dev tools. (The
    dev tools sidebar is visible on the right-hand-side when running your
    project using `rio run`.)

    The set name and variant can be omitted. If no set name is specified, it
    defaults to `material`. If no variant is specified, the default version of
    the icon, i.e. no variant, is used.


    ## Attributes

    `icon`: The name of the icon to display, in the format
        `icon-set/name:variant`. You can browse all available icons in Rio's
        dev tools sidebar.

    `fill`: The color scheme of the icon. The text color is used if no fill is
        specified.


    ## Examples

    This minimal example will display the icon named "castle" from the
    "material" icon set:

    ```python
    rio.Icon("material/castle")
    ```

    You can also specify the color, width and height of the icon:

    ```python
    rio.Icon(
        "material/castle",
        fill=rio.Color.from_hex("ff0000"),
        height=2.5,
        width=2.5,
    )
    ```
    """

    icon: str
    _: KW_ONLY
    fill: _IconFill

    @staticmethod
    @deprecations.deprecated(since="0.9.1", replacement=icons.register_icon_set)
    def register_icon_set(
        set_name: str,
        icon_set_archive_path: Path,
    ) -> None:
        icons.register_icon_set(set_name, icon_set_archive_path)

    @staticmethod
    @deprecations.deprecated(since="0.9.1", replacement=icons.register_icon)
    def register_single_icon(
        icon_source: Path,
        set_name: str,
        icon_name: str,
        variant_name: str | None = None,
    ) -> None:
        icons.register_icon(icon_source, set_name, icon_name, variant_name)

    def __init__(
        self,
        icon: str,
        *,
        fill: _IconFill = "keep",
        key: str | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        width: float | Literal["grow"] = 1.3,
        height: float | Literal["grow"] = 1.3,
        align_x: float | None = None,
        align_y: float | None = None,
    ):
        super().__init__(
            key=key,
            margin=margin,
            margin_x=margin_x,
            margin_y=margin_y,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            width=width,
            height=height,
            align_x=align_x,
            align_y=align_y,
        )

        self.icon = icon
        self.fill = fill

    def _custom_serialize(self) -> JsonDoc:
        # Serialize the fill. This isn't automatically handled because it's a
        # Union.
        fill = self.fill
        if not isinstance(fill, str):
            fill = self.session._serialize_fill(fill)

        # Serialize
        return {
            "fill": fill,
        }


Icon._unique_id = "Icon-builtin"
