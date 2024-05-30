import subprocess
import sys

import revel

DEV_BRANCH = "dev"
RELEASE_BRANCH = "main"


def main() -> None:
    revel.print("Running sanity checks...")

    ensure_branch(DEV_BRANCH)
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
    if process.returncode != 0:
        revel.fatal("The test suite does not pass")


def make_new_release() -> None:
    # Bump the version
    version_part_to_bump = revel.select(
        {
            "patch": "patch",
            "minor": "minor",
            "major": "major",
        },
        prompt="Which version do you want to bump?",
    )
    subprocess.run(
        [sys.executable, "-m", "hatch", "version", version_part_to_bump],
        check=True,
    )
    subprocess.run(["git", "commit", "--all", "-m", "bump version"], check=True)
    subprocess.run(["git", "push"], check=True)

    # Merge DEV_BRANCH into RELEASE_BRANCH and push
    subprocess.run(
        ["git", "fetch", ".", f"{DEV_BRANCH}:{RELEASE_BRANCH}"], check=True
    )
    subprocess.run(["git", "push", "-u", "origin", RELEASE_BRANCH], check=True)

    # Publish
    subprocess.run(["rye", "build", "--clean"], check=True)
    subprocess.run(["rye", "publish"], check=True)


if __name__ == "__main__":
    main()
