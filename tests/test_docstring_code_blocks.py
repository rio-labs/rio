import json
import re
import subprocess
import sys
import tempfile
import textwrap
import typing as t
from pathlib import Path

import pytest

import rio.docs

CODE_BLOCK_PATTERN = re.compile(r"```(.*?)```", re.DOTALL)


all_documented_objects = list(rio.docs.find_documented_objects())
all_documented_objects.sort(key=lambda obj: obj.__name__)


def ruff(*args: str | Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "ruff", *map(str, args)],
        # check=True,
        capture_output=True,
        text=True,
    )


def get_code_blocks(obj: type | t.Callable) -> list[str]:
    """
    Returns a list of all code blocks in the docstring of a component.
    """
    docstring = obj.__doc__

    # No docs?
    if not docstring:
        return []

    docstring = textwrap.dedent(docstring)

    # Find any contained code blocks
    result: list[str] = []
    for match in CODE_BLOCK_PATTERN.finditer(docstring):
        block: str = match.group(1)

        # Split into language and source
        linebreak = block.find("\n")
        assert linebreak != -1
        language = block[:linebreak]
        block = block[linebreak + 1 :]

        # Make sure a language is specified
        assert language, "The code block has no language specified"

        result.append(block)

    return result


def ruff_format(source_code: str) -> str:
    # Write the source code to a temporary file
    temp_file_path = Path(tempfile.gettempdir()) / "rio test suite tempfile.py"

    temp_file_path.write_text(source_code, encoding="utf8")

    # Run ruff to format the source code in the temporary file
    ruff("format", temp_file_path)

    # Read the formatted source code
    return temp_file_path.read_text(encoding="utf8")


def ruff_check(source_code: str) -> list[str]:
    """
    Checks the given source code using `ruff`. Returns any encountered problems.
    """
    # Dump the source to a file, and implicitly define/import some stuff
    temp_file_path = Path(tempfile.gettempdir()) / "rio test suite tempfile.py"

    temp_file_path.write_text(
        f"""
import pathlib
import rio

# Importing `Path` directly causes ruff to complain about a redefinition
Path = pathlib.Path
self = rio.Spacer()

{source_code}
""",
        encoding="utf8",
    )

    # Run ruff to format the source code in the temporary file
    proc = ruff(
        "check",
        temp_file_path,
        "--ignore=E402",  # Caused by the injected imports
        "--output-format=json",
    )

    output = json.loads(proc.stdout)
    assert isinstance(output, list), output

    # Parse the output
    result: list[str] = []

    for entry in output:
        result.append(entry["message"])

    return result


@pytest.mark.parametrize("obj", all_documented_objects)
def test_code_block_is_formatted(obj: type | t.Callable) -> None:
    # Make sure all code blocks are formatted according to ruff
    for source in get_code_blocks(obj):
        formatted_source = ruff_format(source)

        # Ruff often inserts 2 empty lines between definitions, but that's
        # really not necessary in docstrings. Collapse them to a single empty
        # line.
        source = source.replace("\n\n\n", "\n\n")
        formatted_source = formatted_source.replace("\n\n\n", "\n\n")

        assert formatted_source == source


@pytest.mark.parametrize("obj", all_documented_objects)
def test_analyze_code_block(obj: type | t.Callable) -> None:
    # A lot of snippets are missing context, so it's only natural that ruff will
    # find issues with the code. There isn't really anything we can do about it,
    # so we'll just skip those object.
    if obj in (
        rio.App,
        rio.Color,
        rio.UserSettings,
    ):
        pytest.xfail()

    # Make sure ruff is happy with all code blocks
    for source in get_code_blocks(obj):
        errors = ruff_check(source)
        assert not errors, errors
