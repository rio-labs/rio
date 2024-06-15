from __future__ import annotations

import logging
import re
import tarfile
from pathlib import Path
from typing import *  # type: ignore

import introspection

from .. import utils
from ..errors import AssetError

# Maps icon names (set/icon:variant) to the icon's SVG string. The icon
# names are canonical form.
cached_icons: dict[str, str] = {}

# Maps icon set names to the path of the archive file containing the icons
icon_set_archives: dict[str, Path] = {
    "material": utils.RIO_ASSETS_DIR / "icon-sets" / "material.tar.xz",
    "rio": utils.RIO_ASSETS_DIR / "icon-sets" / "rio.tar.xz",
    "styling": utils.RIO_ASSETS_DIR / "icon-sets" / "styling.tar.xz",
}


def parse_icon_name(icon_name: str) -> tuple[str, str, str | None]:
    """
    Given a name for an icon, return the three parts of the name: set, icon,
    variant. If the name is syntactically invalid (e.g. too many slashes),
    raise an `AssetError`.
    """
    # Determine the icon set
    sections = icon_name.split("/")

    if len(sections) == 1:
        icon_set = "material"
        icon_name = sections[0]
    elif len(sections) == 2:
        icon_set, icon_name = sections
    else:
        raise AssetError(
            f"Invalid icon name `{icon_name}`. Icons names must be of the form `set/icon:variant`"
        )

    # Determine the icon name and variant
    sections = icon_name.split(":")

    if len(sections) == 1:
        return icon_set, sections[0], None

    if len(sections) == 2:
        return icon_set, sections[0], sections[1]

    raise AssetError(
        f"Invalid icon name `{icon_name}`. Icons names must be of the form `set/icon:variant`"
    )


def normalize_icon_name(icon_name: str) -> str:
    """
    Given a name for an icon, return the canonical form of the name. If the
    name is syntactically invalid (e.g. too many slashes), raise an
    `AssetError`.
    """

    set, name, section = parse_icon_name(icon_name)

    if section is None:
        return f"{set}/{name}"

    return f"{set}/{name}:{section}"


def _icon_set_extraction_dir(icon_set: str) -> Path:
    """
    Given the name of an icon set, return the directory where the icon set
    will be extracted to. The directory will be created if necessary.
    """
    return utils.ASSET_MANGER.get_cache_path(
        Path("icon-sets") / icon_set,
    )


def _ensure_icon_set_is_extracted(icon_set: str) -> None:
    """
    Given the name of an icon set, extract the icon set's archive to the
    cache directory. The target director must not exist yet. Raises a
    `KeyError` if no icon set with the given name has been registered.
    """
    # If the target directory already exists there is nothing to do
    icon_set_dir = _icon_set_extraction_dir(icon_set)

    if icon_set_dir.exists():
        return

    # Get the path to the icon set's archive. If there is no icon set with
    # the given name, this will raise a `KeyError`. That's fine.
    archive_path = icon_set_archives[icon_set]

    # Extract the set
    logging.debug(
        f"Extracting icon set `{icon_set}` from `{archive_path}` to `{icon_set_dir}`"
    )

    with tarfile.open(archive_path, "r:xz") as tar_file:
        tar_file.extractall(icon_set_dir.parent)

    # Sanity check: Make sure the target directory exists now
    if not icon_set_dir.exists():
        raise RuntimeError(
            f"After extracting icon set `{icon_set}` from `{archive_path}` to `{icon_set_dir.parent}`, the target directory does not exist. Is the directory in the archive named correctly?"
        )


def _get_icon_svg_path(icon_name: str) -> Path:
    """
    Given an icon name, return the path to the SVG file for that icon. This
    will extract the icon if necessary.
    """
    # Prepare some paths
    icon_set, icon_name, variant = parse_icon_name(icon_name)

    icon_set_dir = _icon_set_extraction_dir(icon_set)

    if variant is None:
        svg_path = icon_set_dir / f"{icon_name}.svg"
    else:
        svg_path = icon_set_dir / variant / f"{icon_name}.svg"

    # Extract the icon set if necessary
    try:
        _ensure_icon_set_is_extracted(icon_set)
    except KeyError:
        raise AssetError(
            f"No icon set with the name {icon_set!r} is registered"
        )

    if not svg_path.exists():
        raise AssetError(f"There is no icon named {icon_name!r}")

    return svg_path


def get_icon_svg(icon_name: str) -> str:
    """
    Given an icon name, return the SVG string for that icon. This will
    extract the icon if necessary. If the icon name is invalid or there is
    no matching icon, raise an `AssetError`.
    """

    # Normalize the icon name
    icon_name = normalize_icon_name(icon_name)

    # Already cached?
    try:
        return cached_icons[icon_name]
    except KeyError:
        pass

    # Get the path to the icon's SVG file
    svg_path = _get_icon_svg_path(icon_name)

    # Read the SVG file
    try:
        svg_string = svg_path.read_text()
    except FileNotFoundError:
        # Figure out which part of the name is the problem to show a
        # descriptive error message
        icon_set, icon_name, variant = parse_icon_name(icon_name)

        icon_set_dir = _icon_set_extraction_dir(icon_set)

        if not icon_set_dir.exists():
            raise AssetError(
                f"Unknown icon set `{icon_set}`. Known icon sets are: `{'`, `'.join(icon_set_archives.keys())}`"
            ) from None

        raise AssetError(
            f"There is no icon named `{icon_name}` in the `{icon_set}` icon set"
        ) from None

    # Cache the icon
    cached_icons[icon_name] = svg_string

    # Done
    return svg_string


def _get_variant_directories(
    icon_set: str,
) -> Iterable[tuple[str | None, Path]]:
    """
    Given the name of an icon set, list the names of all variants in that
    set along with the directory they are stored in.
    """

    # Make sure the icon set is extracted
    _ensure_icon_set_is_extracted(icon_set)

    # Iterate over all files in the icon set directory. Directories
    # correspond to variants. If icons are found in the root directory, they
    # are part of the default variant.
    icon_set_dir = _icon_set_extraction_dir(icon_set)
    has_default_variant = False

    for path in icon_set_dir.iterdir():
        if path.is_dir():
            yield (path.name, path)
        else:
            has_default_variant = True

    if has_default_variant:
        yield (None, icon_set_dir)


def all_icon_sets() -> Iterable[str]:
    """
    Return the names of all icon set names known to rio.
    """
    return icon_set_archives.keys()


def all_variants_in_set(icon_set: str) -> Iterable[str | None]:
    """
    Given the name of an icon set, list the names of all variants in that
    set.
    """
    for name, _ in _get_variant_directories(icon_set):
        yield name


def all_icons_in_set(
    icon_set: str,
    *,
    variant: str | None = None,
) -> Iterable[tuple[str, str | None]]:
    """
    Given the name of an icon set, list all icon names and variants in that
    set. If `variant` is given, only return icons with that variant.
    Otherwise, icons of all variants are returned.

    ## Raises

    `KeyError`: if there is not icon set or variant with the given name.
    """
    # Find all available variants. This will also extract the icon set if
    # necessary.
    variants = dict(_get_variant_directories(icon_set))

    # Apply the variant filter. Any `KeyError` is propagated.
    if variant is not None:
        variants = {variant: variants[variant]}

    # Iterate over all variants
    for variant_name, path in variants.items():
        for icon_path in path.iterdir():
            # Only care for SVG files
            if icon_path.is_dir() or icon_path.suffix != ".svg":
                continue

            # Yield
            icon_name = icon_path.stem
            yield icon_name, variant_name


NUMBER_REGEX = re.compile(r"\d+")


def icon_name_to_attr_name(
    icon_name: str, *, variant: str | None = None
) -> str:
    attr_name = introspection.convert_case(icon_name, "snake")

    # Convert leading numbers to english
    match = NUMBER_REGEX.match(attr_name)
    if match:
        number = match.group()
        attr_name = _number_to_english(number) + "_" + attr_name[match.end() :]

    if variant:
        attr_name += "_" + introspection.convert_case(variant, "snake")

    return attr_name


def _number_to_english(number: str) -> str:
    return {
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
        "10": "ten",
        "11": "eleven",
        "12": "twelve",
        "13": "thirteen",
        "14": "fourteen",
        "15": "fifteen",
        "16": "sixteen",
        "17": "seventeen",
        "18": "eighteen",
        "19": "nineteen",
        "20": "twenty",
        "21": "twenty_one",
        "22": "twenty_two",
        "23": "twenty_three",
        "24": "twenty_four",
        "30": "thirty",
        "40": "forty",
        "50": "fifty",
        "60": "sixty",
        "123": "hundred_twenty_three",
        "360": "three_sixty",
    }.get(number, number)
