import collections
import contextlib
import sys
import tarfile
from pathlib import Path

import introspection
import revel

app_name = Path(__file__).stem
app = revel.App(
    nicename=app_name,
    command_name=app_name,
)


@app.command()
def create(archive_file: str, output_file: str | None = None) -> None:
    if output_file is None:
        outfile_ctx = contextlib.nullcontext(sys.stdout)
    else:
        outfile_ctx = open(output_file, "w", encoding="utf8")

    icon_set_name, _, _ = Path(archive_file).name.partition(".")
    icon_set_name = introspection.convert_case(icon_set_name, "snake")

    icons = collect_icons(archive_file)

    with outfile_ctx as outfile:
        outfile.write("import typing as t\n\n")

        icon_set_name_pascal = introspection.convert_case(
            icon_set_name, "pascal"
        )
        outfile.write(f"{icon_set_name_pascal}Icon = t.Literal[\n")

        for icon_name in sorted(icons):
            variants = sorted(
                introspection.convert_case(variant, "snake")
                for variant in icons[icon_name]
            )
            icon_name = introspection.convert_case(icon_name, "snake")

            for variant in variants:
                if variant:
                    print(
                        f'    "{icon_set_name}/{icon_name}:{variant}",',
                        file=outfile,
                    )
                else:
                    print(
                        f'    "{icon_set_name}/{icon_name}",',
                        file=outfile,
                    )

        outfile.write("]\n")


def collect_icons(archive_file: str) -> dict[str, list[str]]:
    # Map icons to their variants
    icons = collections.defaultdict[str, list[str]](list)

    with tarfile.open(archive_file) as archive:
        for member in archive.getmembers():
            try:
                (icon_set_name, icon_or_variant, *icon) = member.name.split("/")
            except ValueError:
                # The root directory only has 1 path segment, so it throws a
                # ValueError. Skip it.
                continue

            # If `icon` is not empty, then this is an icon with a variant
            if icon:
                icon_name = Path(icon[0]).stem
                icons[icon_name].append(icon_or_variant)
                continue

            # If it's a directory, it's a variant folder. Skip it.
            if member.isdir():
                continue

            # If it's a file, it's an icon with no variant
            icon_name = Path(icon_or_variant).stem
            icons[icon_name].append("")

    return icons


if __name__ == "__main__":
    app.run()
