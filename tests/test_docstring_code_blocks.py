import json
import re
import subprocess
import tempfile
import textwrap
from typing import *  # type: ignore

import black
import pytest

import rio.docs

CODE_BLOCK_PATTERN = re.compile(r"```(.*?)```", re.DOTALL)


all_documented_objects = [obj for obj, _ in rio.docs.find_documented_objects()]
all_documented_objects.sort(key=lambda obj: obj.__name__)


def get_code_blocks(obj: type | Callable) -> list[str]:
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


# def format_with_ruff(source_code: str) -> str:
#     # Write the source code to a temporary file
#     with tempfile.NamedTemporaryFile(suffix=".py", mode="w") as temp_file:
#         temp_file.write(source_code)
#         temp_file.flush()

#         # Run ruff to format the source code in the temporary file
#         subprocess.run(["ruff", "format", temp_file.name, "--fix"], check=True)

#         # Read the formatted source code
#         with open(temp_file.name, "r") as temp_file:
#             return temp_file.read()


def check_with_ruff(source_code: str) -> list[str]:
    """
    Checks the given source code using `ruff`. Returns any encountered problems.
    """
    # Dump the source to a file, and implicitly define/import some stuff
    with tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", encoding="utf-8"
    ) as temp_file:
        temp_file.write(
            f"""
import pathlib
import rio

# Importing `Path` directly causes ruff to complain about a redefinition
Path = pathlib.Path
self = rio.Spacer()

{source_code}
"""
        )
        temp_file.flush()

        # Run ruff to format the source code in the temporary file
        proc = subprocess.run(
            [
                "python",
                "-m",
                "ruff",
                "check",
                temp_file.name,
                "--ignore=E402",  # Caused by the injected imports
                "--output-format=json",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        output = json.loads(proc.stdout)
        assert isinstance(output, list), output

    # Parse the output
    result: list[str] = []

    for entry in output:
        result.append(entry["message"])

    return result


@pytest.mark.parametrize("obj", all_documented_objects)
def test_eval_code_block(obj: type | Callable) -> None:
    # Eval all code blocks and make sure they don't crash
    for source in get_code_blocks(obj):
        compile(source, "<string>", "exec")


@pytest.mark.parametrize("obj", all_documented_objects)
def test_code_block_is_formatted(obj: type | Callable) -> None:
    # Make sure all code blocks are formatted according to black
    for source in get_code_blocks(obj):
        formatted_source = black.format_str(source, mode=black.FileMode())

        # Black often inserts 2 empty lines between stuff, but that's really not
        # necessary in docstrings. So we'll collapse those into a single empty
        # line.
        source = source.replace("\n\n\n", "\n\n")
        formatted_source = formatted_source.replace("\n\n\n", "\n\n")

        assert source == formatted_source


PYRIGHT_ERROR_OR_WARNING_REGEX = re.compile(
    r".*\.py:\d+:\d+ - (?:error|warning): (.*)"
)


@pytest.mark.parametrize("obj", all_documented_objects)
def test_analyze_code_block(obj: type | Callable) -> None:
    # A lot of snippets are missing context, so it's only natural that pyright
    # will find issues with the code. There isn't really anything we can do
    # about it, so we'll just skip those object.
    if obj in (rio.App, rio.Color, rio.UserSettings):
        pytest.xfail()

    # Make sure pyright is happy with all code blocks
    for source in get_code_blocks(obj):
        errors = check_with_ruff(source)
        assert not errors, errors
