import subprocess
import sys
from pathlib import Path

import requests
import revel

import rio

PROJECT_DIR = Path(__file__).absolute().parent.parent


def main() -> None:
    revel.print("Running sanity checks...")

    # Make sure we're on the correct branch
    process = subprocess.run(
        ["git", "branch", "--show-current"],
        check=True,
        capture_output=True,
        text=True,
    )
    if process.stdout.strip("\n") != "dev":
        revel.fatal("You must checkout the 'dev' branch")

    # Make sure the version number got bumped
    if rio.__version__ == get_latest_published_version():
        revel.fatal("You forgot to increment the version number")

    # Build the TS code
    subprocess.run(["rye", "run", "build"], check=True)

    # Run the test suite
    if tests_pass():
        revel.print("Everything is in order. Publishing...")
    else:
        # revel.fatal("The test don't pass")
        if not revel.select_yes_no(
            "The test suite does not pass. Do you want to publish anyway?"
        ):
            sys.exit(1)

        revel.print("Publishing...")

    # Merge dev into main and push
    subprocess.run(["git", "fetch", ".", "dev:main"], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)

    # Publish
    subprocess.run(["rye", "build", "--clean"], check=True)
    subprocess.run(["rye", "publish"], check=True)


def get_latest_published_version() -> str:
    response = requests.get(f"https://pypi.org/pypi/rio-ui/json")
    return response.json()["info"]["version"]


def tests_pass() -> bool:
    return subprocess.run(["rye", "test", "--", "-x"]) == 0


if __name__ == "__main__":
    main()
