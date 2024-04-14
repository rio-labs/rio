import subprocess
import tomllib
from pathlib import Path

import pytest
import requests
import revel

PROJECT_DIR = Path(__file__).absolute().parent.parent


def main() -> None:
    # Make sure we're on the correct branch
    process = subprocess.run(
        ["git", "branch"], check=True, capture_output=True, text=True
    )
    if process.stdout.strip("\n") != "dev":
        revel.fatal("You must checkout the 'dev' branch")

    # Make sure the version number got bumped
    version = get_current_version()
    if version == get_latest_published_version():
        revel.fatal("You forgot to increment the version number")

    # Build the TS code
    subprocess.run(["npm", "run", "build"], check=True)

    # Run the test suite
    if not tests_pass():
        revel.fatal("The test don't pass")

    # Merge dev into main and push
    subprocess.run(["git", "fetch", ".", "dev:main"], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)

    # Publish
    subprocess.run(["poetry", "publish"], check=True)


def get_latest_published_version() -> str:
    response = requests.get(f"https://pypi.org/pypi/rio-ui/json")
    return response.json()["info"]["version"]


def get_current_version() -> str:
    with open(PROJECT_DIR / "pyproject.toml", "rb", encoding="utf8") as file:
        data = tomllib.load(file)

    return data["tool"]["poetry"]["version"]


def tests_pass() -> bool:
    return pytest.main([str(PROJECT_DIR / "tests")]) == 0


main()
