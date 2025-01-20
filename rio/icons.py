from pathlib import Path

from . import deprecations, icon_registry

__all__ = ["register_icon_set", "register_icon"]


@deprecations.deprecated(
    since="0.9.2",
    replacement="rio.Icon.register_icon_set",
)
def register_icon_set(
    set_name: str,
    set_archive_path: Path,
) -> None:
    """
    Add an icon set to the global registry. This allows the icons to be accessed
    as `"icon_set/icon_name"` or `"icon_set/icon_name:variant"`.

    There must not already be a set with the given name.

    The icon set is a `.tar.xz` compressed archive and must contain exactly one
    directory, which must be named identically to the icon set. Files located in
    the root of that directory can be accessed as `"icon_set/icon_name"`. Files
    located in a subdirectory can be accessed as `"icon_set/icon_name:variant"`.

    For SVG files to work as icons...

    - They must have a `viewBox` attribute, but no height or width
    - They must contain exactly one XML root node: `<svg>...</svg>`. This also
      goes for comments!
    - Rio colors paths by assigning a `fill` to the SVG root. This only works as
      long as the SVG paths don't have a `<style>` assigned already.


    ## Parameters

    `set_name`: The name of the new icon set. This will be used to access
        the icons.

    `set_archive_path`: The path to the `.tar.xz` archive containing the
        icon set.
    """
    if set_name in icon_registry.icon_set_archives:
        raise ValueError(f"There is already an icon set named `{set_name}`")

    icon_registry.icon_set_archives[set_name] = set_archive_path


@deprecations.deprecated(since="0.9.2", replacement="rio.Icon.register_icon")
def register_icon(
    icon_source: Path,
    set_name: str,
    icon_name: str,
    variant_name: str | None = None,
) -> None:
    """
    Add a single icon to the global registry. This allows the icon to be
    accessed as `"icon_set/icon_name"` or `"icon_set/icon_name:variant"`.

    `icon_source` needs to be the path to a single SVG file. For SVG files
    to work as icons...

    - They must have a `viewBox` attribute, but no height or width
    - They must contain exactly one XML root node: `<svg>...</svg>`. This
      also goes for comments!
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

    # Try to load the icon
    svg_source = icon_source.read_text(encoding="utf8")

    # Add it to the icon registry's cache
    if variant_name is None:
        name = f"{set_name}/{icon_name}"
    else:
        name = f"{set_name}/{icon_name}:{variant_name}"

    icon_registry.cached_icons[name] = svg_source
