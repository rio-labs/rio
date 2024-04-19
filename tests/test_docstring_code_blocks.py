import re
import subprocess
import tempfile
from typing import *  # type: ignore

import black
import imy.docstrings
import pyright
import pytest

import rio

CODE_BLOCK_PATTERN = re.compile(r"```.*?\n(.*?)\n```", re.DOTALL)


def all_components() -> list[Type[rio.Component]]:
    """
    Iterates over all components that ship with Rio.
    """
    to_do: Iterable[Type[rio.Component]] = [rio.Component]
    result: list[Type[rio.Component]] = []

    while to_do:
        component = to_do.pop()
        result.append(component)
        to_do.extend(component.__subclasses__())

    return result


def get_code_blocks(comp: Type[rio.Component]) -> list[str]:
    """
    Returns a list of all code blocks in the docstring of a component.
    """
    docs = imy.docstrings.ClassDocs.from_class(comp)

    # No docs?
    if docs.details is None:
        return []

    # Find any contained code blocks
    result: list[str] = []
    for match in CODE_BLOCK_PATTERN.finditer(docs.details):
        block: str = match.group(0)

        assert block.startswith("```")
        assert block.endswith("```")

        # Split into language and source
        linebreak = block.index("\n")
        assert linebreak != -1
        first_line = block[3:linebreak].strip()
        block = block[linebreak + 1 : -3]

        # Make sure a language is specified
        assert first_line, "The code block has no language specified"

        result.append(block)

    return result


@pytest.mark.parametrize("comp", all_components())
def test_eval_code_block(comp: Type[rio.Component]) -> None:
    # Eval all code blocks and make sure they don't crash
    for source in get_code_blocks(comp):
        compile(source, "<string>", "exec")


@pytest.mark.parametrize("comp", all_components())
def test_code_block_is_formatted(comp: Type[rio.Component]) -> None:
    # Make sure all code blocks are formatted according to black
    for source in get_code_blocks(comp):
        formatted_source = black.format_str(source, mode=black.FileMode())
        assert source == formatted_source


def _pyright_check_source(source: str) -> tuple[int, int]:
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
            f.name,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result_out = proc.stdout
        assert isinstance(result_out, bytes), type(result_out)
        result_out = result_out.decode()

        # Find the number of errors and warnings
        match = re.search(
            r"(\d+) error(s)?, (\d+) warning(s)?, (\d+) information",
            result_out,
        )
        assert match is not None, result_out
        return int(match.group(1)), int(match.group(3))


@pytest.mark.parametrize("comp", all_components())
def test_analyze_code_block(comp: Type[rio.Component]) -> None:
    # Make sure pyright is happy with all code blocks
    for source in get_code_blocks(comp):
        n_errors, n_warnings = _pyright_check_source(source)

        assert n_errors == 0, f"Found {n_errors} errors"
        assert n_warnings == 0, f"Found {n_warnings} warnings"
