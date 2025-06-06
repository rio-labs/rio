import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import build as build_frontend
import revel

import rio.cli.project_setup
import rio.snippets
from rio.version import Version


def main() -> None:
    # Sanity checks
    revel.print_chapter("Running sanity checks")

    ensure_branch("main")
    ensure_no_uncommitted_changes()
    ensure_up_to_date_with_remote()

    build_frontend.build_frontend(mode="release")
    if "--skip-tests" not in sys.argv:
        ensure_tests_pass()

    revel.success("Everything is in order.")

    # Update the templates repository
    revel.print_chapter("Updating templates repository")
    publish_current_templates()

    # Publish
    revel.print_chapter("Building & Publishing release")
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


def ensure_tests_pass() -> None:
    process = subprocess.run(
        ["uv", "run", "--", "pytest", "tests", "-x", "--disable-warnings"]
    )

    if process.returncode == 0:
        revel.print("Everything is in order. Publishing...")
    else:
        if not revel.select_yes_no(
            "The test suite does not pass. Do you want to publish anyway?"
        ):
            sys.exit(1)

        revel.print("Publishing...")


def has_git_changes() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(result.stdout.strip())


def publish_current_templates() -> None:
    """
    All of Rio's built-in templates are available in source code form in a
    public repository. This allows users to browse the code. This function
    ensures that the latest versions of all templates are available in the
    repository.

    It's unclear whether this function should be in the `rio` project itself, or
    the website. While not strongly linked to the website, having the repository
    update here ensures that the links on the Rio website are always correct,
    i.e. all templates that the site links to are also definitely in that
    repository.
    """
    # Check out the repository
    template_repo_dir = Path(tempfile.mkdtemp())

    subprocess.run(
        [
            "git",
            "clone",
            "git@github.com:rio-labs/rio-templates.git",
            str(template_repo_dir),
        ],
        check=True,
    )

    # Wipe the current templates
    keep_files = (
        ".git",
        "LICENSE.txt",
        "README.md",
    )

    for file_path in template_repo_dir.iterdir():
        if file_path.name not in keep_files:
            assert file_path.is_dir(), file_path
            shutil.rmtree(file_path)

    # Save the current working directory
    original_working_directory = os.getcwd()

    # Re-instantiate all templates
    #
    # This prints profusely, so tell it to be quiet
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")

    os.chdir(template_repo_dir)

    for template in rio.snippets.get_project_templates(include_empty=False):
        rio.cli.project_setup.create_project(
            raw_name=template.name,
            type="website",
            template_name=template.name,
            target_parent_directory=template_repo_dir,
        )

    # Commit and push, if there are changes
    subprocess.run(["git", "add", "."], check=True)

    if has_git_changes():
        subprocess.run(["git", "commit", "-m", "Update templates"], check=True)
        subprocess.run(["git", "push"], check=True)

    # Restore previous state
    sys.stdout = original_stdout
    os.chdir(original_working_directory)


def make_new_release() -> None:
    # Bump version
    bump_version()
    subprocess.run(["git", "push"], check=True)

    # Publish

    # Remove old distributions, otherwise uv in its unending wisdom will try to
    # upload them again and crash
    for path in (Path(__file__).absolute().parent.parent / "dist").iterdir():
        path.unlink()

    subprocess.run(["uv", "build"], check=True)
    subprocess.run(["uv", "publish"], check=True)

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
