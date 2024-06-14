import collections
import contextlib
import re
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
    icons = collect_icons(archive_file)

    with outfile_ctx as outfile:
        cls_name = introspection.convert_case(icon_set_name, "pascal")
        for icon_name in sorted(icons):
            attr_name = icon_name_to_attr_name(icon_name)

            variants = sorted(icons[icon_name])
            for variant in variants:
                if variant:
                    variant_snake = introspection.convert_case(variant, "snake")
                    print(
                        f'{attr_name}_{variant_snake} = "{icon_set_name}/{icon_name}:{variant}"',
                        file=outfile,
                    )
                else:
                    print(
                        f'{attr_name} = "{icon_set_name}/{icon_name}"',
                        file=outfile,
                    )


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


NUMBER_REGEX = re.compile(r"\d+")


def icon_name_to_attr_name(icon_name: str) -> str:
    attr_name = introspection.convert_case(icon_name, "snake")

    # Convert leading numbers to english
    match = NUMBER_REGEX.match(attr_name)
    if match:
        number = match.group()
        attr_name = number_to_english(number) + "_" + attr_name[match.end() :]

    return attr_name


def number_to_english(number: str) -> str:
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


if __name__ == "__main__":
    app.run()
