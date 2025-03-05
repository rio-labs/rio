import subprocess
import sys

import revel

from rio.version import Version


def main() -> None:
    revel.print("Running sanity checks...")

    ensure_branch("main")
    ensure_no_uncommitted_changes()
    ensure_up_to_date_with_remote()

    build_frontend()
    ensure_tests_pass()

    revel.print("Everything is in order.")
    make_new_release()


def ensure_branch(branch_name: str) -> None:
    process = subprocess.run(
        ["git", "branch", "--show-current"],
        check=True,
        capture_output=True,
        text=True,
    )
    if process.stdout.strip("\n") != branch_name:
        revel.fatal(f'You must checkout the "{branch_name}" branch')


def ensure_no_uncommitted_changes() -> None:
    process = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        check=True,
        capture_output=True,
        text=True,
    )
    if process.stdout.strip():
        revel.fatal("There are uncommitted changes")


def ensure_up_to_date_with_remote() -> None:
    subprocess.run(["git", "remote", "update"], check=True)
    process = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        check=True,
        capture_output=True,
        text=True,
    )
    if process.stdout.strip():
        revel.fatal("Local branch is not up-to-date with remote")


def build_frontend() -> None:
    subprocess.run(
        ["rye", "run", "build"],
        check=True,
    )


def ensure_tests_pass() -> None:
    process = subprocess.run(["rye", "test", "--", "-x", "--disable-warnings"])

    if process.returncode == 0:
        revel.print("Everything is in order. Publishing...")
    else:
        if not revel.select_yes_no(
            "The test suite does not pass. Do you want to publish anyway?"
        ):
            sys.exit(1)

        revel.print("Publishing...")


def make_new_release() -> None:
    # Bump version
    bump_version()
    subprocess.run(["git", "push"], check=True)

    # Publish
    subprocess.run(["rye", "build", "--clean"], check=True)
    subprocess.run(["rye", "publish"], check=True)

    # Create a tag
    version = str(get_version())
    subprocess.run(["git", "tag", version], check=True)
    subprocess.run(["git", "push", "origin", "tag", version], check=True)


def bump_version() -> None:
    version = get_version()

    options = dict[str, str]()

    if version.rc is None:
        v = version.bump_patch()
        options[f"Patch:    {v}"] = str(v)

        v = v.bump_rc()
        options[f"Patch RC: {v}"] = str(v)

        v = version.bump_minor()
        options[f"Minor:    {v}"] = str(v)

        v = v.bump_rc()
        options[f"Minor RC: {v}"] = str(v)

        v = version.bump_major()
        options[f"Major:    {v}"] = str(v)

        v = v.bump_rc()
        options[f"Major RC: {v}"] = str(v)
    else:
        v = version.bump_rc()
        options[f"RC:    {v}"] = str(v)

        v = version.drop_rc()
        options[f"No RC: {v}"] = str(v)

    new_version = revel.select(options, prompt="Select new version")

    subprocess.run(
        [sys.executable, "-m", "hatch", "version", new_version],
        check=True,
    )
    subprocess.run(
        ["git", "commit", "--all", "-m", f"bump version to {new_version}"],
        check=True,
    )


def get_version() -> Version:
    version_string = subprocess.run(
        [sys.executable, "-m", "hatch", "version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    return Version.parse(version_string)


if __name__ == "__main__":
    main()
