import subprocess
import sys

import revel


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

    # Create a tag
    version = get_version()
    subprocess.run(["git", "tag", version], check=True)
    subprocess.run(["git", "push", "origin", "tag", version], check=True)

    # Publish
    subprocess.run(["rye", "build", "--clean"], check=True)
    subprocess.run(["rye", "publish"], check=True)


def bump_version() -> None:
    options = {
        "patch": "patch",
        "minor": "minor",
        "major": "major",
    }

    version = get_version()
    if "rc" in version:
        options["release candidate"] = "rc"

    version_part_to_bump = revel.select(
        options,
        prompt="Which version do you want to bump?",
    )

    if version_part_to_bump != "rc":
        if revel.select_yes_no("Make this a pre-release?"):
            version_part_to_bump += ",rc"

    subprocess.run(
        [sys.executable, "-m", "hatch", "version", version_part_to_bump],
        check=True,
    )
    subprocess.run(["git", "commit", "--all", "-m", "bump version"], check=True)


def get_version() -> str:
    return subprocess.run(
        [sys.executable, "-m", "hatch", "version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


if __name__ == "__main__":
    main()
