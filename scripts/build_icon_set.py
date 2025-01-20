"""
This file reads all bootstrap icons from their GitHub repository and packs them
into a `.tar.xz` archive that can be used by Rio as icon set.

The repository is expected to be available locally already - this script does
not clone it.
"""

import tarfile
import tempfile
import typing as t
from pathlib import Path
from xml.etree import ElementTree as ET

import revel


def icon_name_from_path(path: Path) -> tuple[str, str | None | None]:
    """
    Configure: Given the path to the icon, return the icon's name and
    optionally variant.

    If `None` is returned the file is skipped.
    """
    # Normalize the name
    name = path.stem
    name = name.replace("-", "_")
    assert all(c.isalnum() or c == "_" for c in name), path

    # See if this is a variant
    known_variants = [
        "fill",
    ]

    for variant in known_variants:
        if name.endswith(f"_{variant}"):
            name = name.removesuffix(f"_{variant}")
            break
    else:
        variant = None

    return name, variant


def build_icon_set(
    *,
    input_files: t.Iterable[Path],
    output_path: Path,
    set_name: str,
    limit: int | None = None,
) -> None:
    """
    Helper function for building Rio compatible icon sets.

    This function reads a list of SVG files, postprocesses them to fit Rio's
    requirements and dumps them into a compressed archive, again matching Rio's
    expectations.

    Depending on how exactly your input SVGs are structured, this may not be
    enough. Feel free to adapt the function to your exact files.

    ## Parameters

    `input_files`: An iterable over the paths to the SVG files to process.
        (`Path.glob` is your friend here)

    `output_path`: The path to the `.tar.xz` archive to write the icon set to.

    `set_name`: The name of the icon set. This will be used to access the icons.

    `limit`: If set to a number, only process this many files. Set to `None` to
        process all files (Useful for debugging).
    """

    # Find all files to process
    in_file_paths = list(input_files)
    revel.print(f"Found {len(in_file_paths)} file(s)")

    # Enforce an order so that the output is deterministic
    in_file_paths.sort()

    # Apply the limit
    if limit is not None:
        in_file_paths = in_file_paths[:limit]
        revel.warning(
            f"Only processing the first {limit} file(s) (set `limit` to `None` to disable)"
        )

    # Process all files and store the results in a temporary directory
    revel.print_chapter("Processing files")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)

        with revel.ProgressBar(max=len(in_file_paths), unit="count") as bar:
            for ii, file_path in enumerate(in_file_paths):
                bar.progress = ii

                # Extract the name and variant of the icon. If this function returns
                # `None` the file is skipped.
                parsed = icon_name_from_path(file_path.resolve())

                if parsed is None:
                    revel.print(f"{file_path.name} -> [bold]skipped[/bold]")
                    continue

                icon_name, icon_variant = parsed
                variant_suffix = (
                    "" if icon_variant is None else f":{icon_variant}"
                )

                revel.print(
                    f"{file_path.name} -> {set_name}/{icon_name}{variant_suffix}"
                )

                # Parse the SVG
                svg_str = file_path.read_text()
                tree = ET.fromstring(svg_str)

                # Strip problematic attributes
                if "width" in tree.attrib:
                    del tree.attrib["width"]

                if "height" in tree.attrib:
                    del tree.attrib["height"]

                if "fill" in tree.attrib:
                    del tree.attrib["fill"]

                if "class" in tree.attrib:
                    del tree.attrib["class"]

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
        revel.print_chapter("Compressing files")

        with tarfile.open(output_path, "w:xz") as out_file:
            out_file.add(tmp_dir, arcname=set_name)

    revel.print_chapter(None)
    revel.success(
        f"[bold]Done![/] You can find the result at [bold]{output_path}[/bold]"
    )


if __name__ == "__main__":
    PROJECT_DIR = Path(__file__).resolve().parent.parent

    # Clone the material-icons repoisitory from GitHub:
    #
    # https://github.com/marella/material-symbols
    # build_icon_set(
    #     input_files=(
    #         PROJECT_DIR
    #         / "thirdparty"
    #         / "material-icons"
    #         / "thirdparty"
    #         / "material-symbols"
    #         / "svg"
    #         / "500"
    #         / "rounded"
    #     ).glob("*.svg"),
    #     output_path=PROJECT_DIR / "material.tar.xz",
    #     set_name="material",
    #     limit=None,
    # )

    # Clone the bootstrap-icons repository from GitHub:
    #
    # https://github.com/twbs/icons
    build_icon_set(
        input_files=(PROJECT_DIR / "thirdparty" / "bootstrap" / "icons").glob(
            "*.svg"
        ),
        output_path=PROJECT_DIR / "bootstrap.tar.xz",
        set_name="bootstrap",
        limit=None,
    )
