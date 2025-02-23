import json
import subprocess
import sys
import tempfile
from pathlib import Path

__all__ = ["ruff_check", "ruff_format"]


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
    # Dump the source to a file, and implicitly define/import some stuff.
    temp_file_path = Path(tempfile.gettempdir()) / "rio test suite tempfile.py"

    temp_file_path.write_text(
        f"""
import asyncio
import pathlib
import rio

Path = pathlib.Path
app = rio.App(build=rio.Spacer)
MyAppRoot = rio.Spacer
self = child1 = child2 = rio.Spacer()

{source_code}
""",
        encoding="utf8",
    )

    # Run ruff to format the source code in the temporary file
    proc = ruff(
        "check",
        temp_file_path,
        # E402 = Import not at top of file
        #
        # F401 = Unused import
        #
        # F811 = Redefinition of a symbol. Happens if the source code already
        # includes one of our injected imports.
        "--ignore=E402,F401,F811",
        "--output-format=json",
    )

    output = json.loads(proc.stdout)
    assert isinstance(output, list), output

    # Parse the output
    return [entry["message"] for entry in output]


def ruff(*args: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ruff", *map(str, args)],
        # check=True,
        capture_output=True,
        text=True,
    )
