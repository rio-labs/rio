import subprocess
from pathlib import Path

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
    subprocess.run(["rye", "run", "build"], check=True)

    # Run the test suite
    if not tests_pass():
        revel.fatal("The test don't pass")

    # Merge dev into main and push
    subprocess.run(["git", "fetch", ".", "dev:main"], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)

    # Publish
    subprocess.run(["rye", "build", "--clean"], check=True)
    subprocess.run(["rye", "build"], check=True)
    subprocess.run(["rye", "publish", "--skip-existing"], check=True)


def get_latest_published_version() -> str:
    response = requests.get(f"https://pypi.org/pypi/rio-ui/json")
    return response.json()["info"]["version"]


def get_current_version() -> str:
    process = subprocess.run(
        ["rye", "version"], capture_output=True, text=True, check=True
    )
    return process.stdout.strip()


def tests_pass() -> bool:
    return subprocess.run(["rye", "test"], check=True) == 0


main()
