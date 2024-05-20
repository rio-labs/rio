import re
import subprocess
import sys
import tempfile
import textwrap
from typing import *  # type: ignore

import black
import pyright
import pytest

import rio.docs

CODE_BLOCK_PATTERN = re.compile(r"```(.*?)```", re.DOTALL)


all_documented_objects = [
    obj for obj, _ in rio.docs.find_documented_objects(False)
]
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


def _find_static_typing_errors(source: str) -> str:
    """
    Run pyright on the given source and return the number of errors and
    warnings.
    """
    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        # Dump the source to a file, and implicitly import rio
        f.write("import rio\n".encode("utf-8"))
        f.write(source.encode("utf-8"))
        f.flush()

        # Run pyright
        proc = pyright.run(
            "--pythonpath",
            sys.executable,
            f.name,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result_out = proc.stdout
        assert isinstance(result_out, bytes), type(result_out)
        result_out = result_out.decode()

        # Find the number of errors and warnings
        lines = list[str]()

        for line in result_out.splitlines():
            match = PYRIGHT_ERROR_OR_WARNING_REGEX.match(line)

            if match:
                lines.append(match.group(1))

        return "\n".join(lines)


@pytest.mark.parametrize("obj", all_documented_objects)
def test_analyze_code_block(obj: type | Callable) -> None:
    # A lot of snippets are missing context, so it's only natural that pyright
    # will find issues with the code. There isn't really anything we can do
    # about it, so we'll just skip those object.
    if obj in (rio.App, rio.Color, rio.UserSettings):
        pytest.xfail()

    # Make sure pyright is happy with all code blocks
    for source in get_code_blocks(obj):
        errors = _find_static_typing_errors(source)
        assert not errors, errors
