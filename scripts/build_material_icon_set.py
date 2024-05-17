"""
This file reads all materials icons/symbols from their github repository and
packs them into a `.tar.xz` archive that can be used by rio as icon set.

The repository is expected to be available locally already - this script does
not clone it.
"""

import re
import tarfile
import tempfile
from pathlib import Path
from typing import *  # type: ignore
from xml.etree import ElementTree as ET

import revel
from revel import *  # type: ignore

import rio

# Configure: The name the resulting icon set will have
SET_NAME = "material"

# Configure: The path to the directory which should be scanned for SVG files.
#
# Repo URL: https://github.com/marella/material-symbols
INPUT_DIR = (
    rio.utils.PROJECT_ROOT_DIR
    / "thirdparty"
    / "material-symbols"
    / "svg"
    / "500"
    / "rounded"
)

# Configure: Any files in the input directory which match this pattern will be
# processed
INPUT_NAME_PATTERN = r"(.+).svg"

# Configure: The output file will be written into this directory as
# <SET_NAME>.tar.xz
OUTPUT_DIR = rio.utils.RIO_ASSETS_DIR / "icon-sets"

# For debugging: Stop after processing this many icons. Set to `None` for no
# limit
LIMIT = None


# Configure: Given the relative path to the icon, return the icon's name and
# optionally variant.
#
# If `None` is returned the file is skipped.
def name_from_icon_path(path: Path) -> tuple[str, str | None | None]:
    # Normalize the name
    name = path.stem
    name = name.replace("_", "-")
    assert all(c.isalnum() or c == "-" for c in name), path

    # See if this is a variant
    known_variants = [
        "fill",
    ]

    for variant in known_variants:
        if name.endswith(f"-{variant}"):
            name = name.removesuffix(f"-{variant}")
            break
    else:
        variant = None

    return name, variant


# == No changes should be required below this line ==


def main() -> None:
    # Find all files in the input directory
    print_chapter("Scanning files")

    if not INPUT_DIR.exists():
        fatal(f"The input directory [bold]{INPUT_DIR}[/bold] does not exist")

    in_files: list[Path] = []
    for path in INPUT_DIR.glob("**/*"):
        if path.is_file() and re.fullmatch(INPUT_NAME_PATTERN, path.name):
            in_files.append(path)

    print(f"Found {len(in_files)} file(s)")

    # Enforce an order so that the output is deterministic
    in_files.sort()

    # Apply the limit
    if LIMIT is not None:
        in_files = in_files[:LIMIT]
        print(f"Limiting to {LIMIT} file(s) (set `LIMIT` to `None` to disable)")

    # Process all files
    print_chapter("Processing files")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)

        with revel.ProgressBar(max=len(in_files), unit="count") as bar:
            for ii, file_path in enumerate(in_files):
                bar.progress = ii

                # Extract the name and variant of the icon. If this function returns
                # `None` the file is skipped.
                parsed = name_from_icon_path(file_path.relative_to(INPUT_DIR))

                if parsed is None:
                    print(f"{file_path.name} -> [bold]skipped[/bold]")
                    continue

                icon_name, icon_variant = parsed
                variant_suffix = (
                    "" if icon_variant is None else f"/{icon_variant}"
                )

                print(f"{file_path.name} -> {icon_name}{variant_suffix}")

                # Parse the SVG
                svg_str = file_path.read_text()
                tree = ET.fromstring(svg_str)

                # Strip the width / height if any
                if "width" in tree.attrib:
                    del tree.attrib["width"]

                if "height" in tree.attrib:
                    del tree.attrib["height"]

                # Determine the output path for this icon
                icon_out_path = tmp_dir

                if icon_variant is not None:
                    icon_out_path /= icon_variant

                icon_out_path /= f"{icon_name}.svg"

                # Suppress weird "ns0:" prefixes everywhere
                ET.register_namespace("", "http://www.w3.org/2000/svg")

                # Write the SVG
                icon_out_path.parent.mkdir(parents=True, exist_ok=True)

                with open(icon_out_path, "w") as f:
                    f.write(
                        ET.tostring(
                            tree,
                            encoding="unicode",
                            default_namespace=None,
                        )
                    )

        # Compress the temporary directory
        print_chapter("Compressing files")
        archive_path = OUTPUT_DIR / f"{SET_NAME}.tar.xz"

        with tarfile.open(archive_path, "w:xz") as out_file:
            out_file.add(tmp_dir, arcname="")

    print_chapter(None)
    print(
        f"[bold]Done![/] You can find the result at [bold]{OUTPUT_DIR.resolve()}/{SET_NAME}.tar.xz[/]"
    )


if __name__ == "__main__":
    main()
