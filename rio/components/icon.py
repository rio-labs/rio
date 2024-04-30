from __future__ import annotations

from dataclasses import KW_ONLY
from pathlib import Path
from typing import Literal, final

from uniserde import JsonDoc

import rio

from .. import color, fills, icon_registry
from .fundamental_component import FundamentalComponent

__all__ = [
    "Icon",
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

    Note that unlike most components in Rio, `Icon` does not have a `natural`
    size, they can be easily be scaled to fit any size. Therefore it defaults to
    a width and height of 1.3, which is a great size when mixing icons with
    text.

    Icon names are in the format `set_name/icon_name:variant`. Rio already ships
    with the `material` icon set, which contains icons in the style of Google's
    Material Design. You can browse all available icons in Rio's debugger
    sidebar. (The debugger sidebar is visible if you run your project using `rio
    run`.)

    The set name and variant can be omitted. If no set name is specified, it
    defaults to `material`. If no variant is specified, the default version of
    the icon, i.e. no variant, is used.


    ## Attributes

    `icon`: The name of the icon to display, in the format
        `icon-set/name:variant`. You can browse all available icons in Rio's
        debugger sidebar.

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
    fill: rio.FillLike | rio.ColorSet | Literal["dim"]

    @staticmethod
    def _get_registry() -> icon_registry.IconRegistry:
        return icon_registry.IconRegistry.get_singleton()

    @staticmethod
    def register_icon_set(
        set_name: str,
        icon_set_archive_path: Path,
    ) -> None:
        """
        Add an icon set to the global registry. This allows the icons to be
        accessed as `icon_name`, `set_name/icon_name` or
        `set_name/icon_name:variant`.

        There must not already be a set with the given name.

        The icon set is a `.tar.xz` compressed archive and must contain exactly
        one directory, which must be named identically to the icon set. Files
        located in the root of that directory can be accessed as
        `set_name/icon_name`. Files located in a subdirectory can be accessed as
        `set_name/icon_name:variant`.

        For SVG files to work as icons...

        - They must have a `viewBox` attribute, but no height or width
        - They must contain exactly one XML root node: `<svg>...</svg>`. This
          also goes for comments!
        - Rio colors paths by assigning a `fill` to the SVG root. This only
          works as long as the SVG paths don't have a `<style>` assigned
          already.

        ## Parameters
            set_name: The name of the new icon set. This will be used to access
                the icons.

            icon_set_archive_path: The path to the `.tar.xz` archive containing
            the icon
                set.
        """
        registry = Icon._get_registry()

        if set_name in registry.icon_set_archives:
            raise ValueError(f"There is already an icon set named `{set_name}`")

        registry.icon_set_archives[set_name] = icon_set_archive_path

    @staticmethod
    def register_single_icon(
        icon_source: Path,
        set_name: str,
        icon_name: str,
        variant_name: str | None = None,
    ) -> None:
        """
        Add a single icon to the global registry. This allows the icon to be
        accessed as `icon_name`, `set_name/icon_name` or
        `set_name/icon_name:variant`.

        `icon_source` needs to be the path to a single SVG file. For SVG files
        to work as icons...

        - They must have a `viewBox` attribute, but no height or width
        - They must contain exactly one XML root node: `<svg>...</svg>`. This
          also goes for comments!
        - Rio colors paths by assigning a `fill` to the SVG root. This only
          works as long as the SVG paths don't have a `<style>` assigned
          already.

        ## Parameters
            icon_source: The path to the SVG file containing the icon.

            set_name: The name of the new icon set. This will be used to access
                the icons.

            icon_name: The name of the icon. This will be used to access the
                icon.

            variant_name: The name of the variant. This will be used to access
                the icon. If not specified, the default variant will be used.
        """

        # Try to load the icon
        svg_source = icon_source.read_text(encoding="utf8")

        # Add it to the icon registry's cache
        if variant_name is None:
            name = f"{set_name}/{icon_name}"
        else:
            name = f"{set_name}/{icon_name}:{variant_name}"

        registry = Icon._get_registry()
        registry.cached_icons[name] = svg_source

    def __init__(
        self,
        icon: str,
        *,
        fill: rio.FillLike | rio.ColorSet | Literal["dim"] = "keep",
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

    def __post_init__(self):
        # Verify that the icon exists. We want to crash now, not during the next
        # refresh.
        registry = Icon._get_registry()
        registry.get_icon_svg(self.icon)

    def _custom_serialize(self) -> JsonDoc:
        registry = Icon._get_registry()
        svg_source = registry.get_icon_svg(self.icon)

        # Serialize the fill. This isn't automatically handled because it's a
        # Union.
        if isinstance(self.fill, fills.Fill):
            fill = self.fill._serialize(self.session)
        elif isinstance(self.fill, color.Color):
            fill = self.fill.rgba
        else:
            assert isinstance(
                self.fill, str
            ), f"Unsupported fill type: {self.fill}"
            fill = self.fill

        # Serialize
        return {
            "svgSource": svg_source,
            "fill": fill,
        }


Icon._unique_id = "Icon-builtin"
