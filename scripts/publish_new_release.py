import subprocess
import sys
from dataclasses import dataclass

import revel
import typing_extensions as te


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
    version = str(get_version())
    subprocess.run(["git", "tag", version], check=True)
    subprocess.run(["git", "push", "origin", "tag", version], check=True)

    # Publish
    subprocess.run(["rye", "build", "--clean"], check=True)
    subprocess.run(["rye", "publish"], check=True)


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
    subprocess.run(["git", "commit", "--all", "-m", "bump version"], check=True)


@dataclass(frozen=True)
class Version:
    major: int
    minor: int = 0
    patch: int = 0
    rc: int | None = None

    @classmethod
    def parse(cls, version_string: str) -> te.Self:
        head, _, tail = version_string.partition("rc")

        if tail:
            rc = int(tail)
        else:
            rc = None

        parts = head.split(".")
        parts += ("0", "0", "0")

        return cls(
            major=int(parts[0]),
            minor=int(parts[1]),
            patch=int(parts[2]),
            rc=rc,
        )

    def bump_major(self) -> te.Self:
        return type(self)(major=self.major + 1)

    def bump_minor(self) -> te.Self:
        return type(self)(major=self.major, minor=self.minor + 1)

    def bump_patch(self) -> te.Self:
        return type(self)(
            major=self.major,
            minor=self.minor,
            patch=self.patch + 1,
        )

    def bump_rc(self) -> te.Self:
        return type(self)(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            rc=0 if self.rc is None else self.rc + 1,
        )

    def drop_rc(self) -> te.Self:
        return type(self)(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            rc=None,
        )

    def __str__(self):
        version_string = f"{self.major}.{self.minor}"

        if self.patch > 0:
            version_string += f".{self.patch}"

        if self.rc is not None:
            version_string += f"rc{self.rc}"

        return version_string


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
