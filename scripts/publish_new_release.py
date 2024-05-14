import subprocess
import sys

import requests
import revel

import rio


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

    # Make sure there are no uncommitted changes
    process = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        check=True,
        capture_output=True,
        text=True,
    )
    if process.stdout.strip():
        revel.fatal("There are uncommitted changes")

    # Make sure the version number got bumped
    if rio.__version__ == get_latest_published_version():
        revel.fatal("You forgot to increment the version number")

    # Build the TS code
    #
    # Note: `shell=True` is required on Windows because `npm` is a `.cmd` file
    # and not a `.exe`
    subprocess.run(["npm", "run", "build"], shell=True, check=True)

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
    process = subprocess.run(["rye", "test", "--", "-x", "--disable-warnings"])
    return process.returncode == 0


if __name__ == "__main__":
    main()
