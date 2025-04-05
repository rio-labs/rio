from __future__ import annotations

import dataclasses
import typing as t
from pathlib import Path

from uniserde import JsonDoc

from .. import color, fills, icon_registry
from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = [
    "Icon",
]


_IconFill = t.Union[
    "fills.SolidFill",
    "fills.LinearGradientFill",
    "fills.ImageFill",
    "color.ColorSet",
    t.Literal["dim"],
]


@t.final
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

    Icon names are in the format `icon_set/icon_name:variant`. Rio already ships
    with the `material` icon set, which contains icons in the style of Google's
    Material Design. You can browse all available icons in Rio's dev tools. (The
    dev tools sidebar is visible on the right-hand-side when running your
    project using `rio run`.)

    The set name and variant can be omitted. If no set name is specified, it
    defaults to `material`. If no variant is specified, the default version of
    the icon, i.e. no variant, is used.

    ## Getting More Icons

    Additional icons are available in other icon packages. For example, we have
    created a [Bootstrap icons](https://icons.getbootstrap.com/) package
    [here](https://github.com/rio-labs/rio-bootstrap).

    _Are you the author of an icons package for Rio? Send us a PR to add it to
    this list!_

    ## Attributes

    `icon`: The name of the icon to display, in the format
        `icon_set/icon_name:variant`. You can browse all available icons in
        Rio's dev tools sidebar.

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
        min_height=2.5,
        min_width=2.5,
    )
    ```
    """

    icon: str
    _: dataclasses.KW_ONLY
    fill: _IconFill

    @staticmethod
    def register_icon_set(
        set_name: str,
        set_archive_path: Path,
    ) -> None:
        """
        Adds an icon set to the global registry. This allows the icons to be
        accessed as `"icon_set/icon_name"` or `"icon_set/icon_name:variant"`.

        There must not already be a set with the given name.

        The icon set must be a `.tar.xz` compressed archive containing exactly
        one directory, which must be named identically to the icon set. Files
        located in the root of that directory can be accessed as
        `"icon_set/icon_name"`. Files located in a subdirectory can be accessed
        as `"icon_set/icon_name:variant"`.

        For SVG files to work as icons...

        - They must have a `viewBox` attribute, but no height or width
        - They must contain exactly one XML root node: `<svg>...</svg>`.
          Comments also count!
        - Rio colors paths by assigning a `fill` to the SVG root. This only
          works as long as the SVG paths don't have a `<style>` assigned already.


        ## Parameters

        `set_name`: The name of the new icon set. This will be used to access
            the icons.

        `set_archive_path`: The path to the `.tar.xz` archive containing the
            icon set.
        """

        icon_registry.register_icon_set(set_name, set_archive_path)

    @staticmethod
    def register_single_icon(
        icon_source: Path,
        set_name: str,
        icon_name: str,
        variant_name: str | None = None,
    ) -> None:
        """
        Adds a single icon to the global registry. This allows the icon to be
        accessed as `"icon_set/icon_name"` or `"icon_set/icon_name:variant"`.

        If another icon was already registered with the same set, name and
        variant it will be overwritten.

        `icon_source` needs to be the path to a single SVG file. For SVG files
        to work as icons, they need to meet some conventions:

        - They must have a `viewBox` attribute, but no height or width
        - They must contain exactly one XML root node: `<svg>...</svg>`.
          Comments also count!
        - Rio colors paths by assigning a `fill` to the SVG root. This only
        works as long as the SVG paths don't have a `<style>` assigned
        already.


        ## Parameters

        `icon_source`: The path to the SVG file containing the icon.

        `set_name`: The name of the new icon set. This will be used to access
            the icons.

        `icon_name`: The name of the icon. This will be used to access the
            icon.

        `variant_name`: The name of the variant. This will be used to access
            the icon. If not specified, the default variant will be used.
        """

        icon_registry.register_single_icon(
            icon_source, set_name, icon_name, variant_name
        )

    def __init__(
        self,
        icon: str,
        *,
        fill: _IconFill = "keep",
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_width: float = 1.3,
        min_height: float = 1.3,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
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
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
            align_x=align_x,
            align_y=align_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
            accessibility_role=accessibility_role,
        )

        self.icon = icon
        self.fill = fill

    def __post_init__(self) -> None:
        # Verify that the icon exists. This makes sure any crashes happen
        # immediately, rather than during the next refresh.
        icon_registry.get_icon_svg(self.icon)

    def _custom_serialize_(self) -> JsonDoc:
        # Serialize the fill. This isn't automatically handled because it's a
        # Union.
        fill = self.fill
        if not isinstance(fill, str):
            fill = self.session._serialize_fill(fill)

        # Serialize
        return {
            "fill": fill,
        }


Icon._unique_id_ = "Icon-builtin"
