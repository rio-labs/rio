import asyncio
import random
import re
import tarfile
import tempfile
from pathlib import Path
from typing import *  # type: ignore

import revel
from revel import input, print, print_chapter, warning

import rio.cli
from rio.cli.rio_api import RioApi


def should_directory_likely_be_excluded(
    dir_path: Path,
) -> tuple[str, str] | None:
    """
    Some directories should very likely not be part of the user's project. This
    function looks at a directory, and if the directory should likely be
    excluded it returns a name and explanation of why. Returns `None` otherwise.
    """
    assert dir_path.is_dir(), dir_path

    # Virtual environments
    if (dir_path / "pyvenv.cfg").exists():
        return (
            "contain a python virtual environment",
            "Virtual environments contain a huge number of files which are typically created by `pip`, `poetry`, `conda` or similar. These don't have to be included with your project and can easily be recreated later.",
        )

    # .git
    if dir_path.name == ".git":
        return (
            "be a git folder",
            "Git repositories contain the entire history of your project and typically aren't necessary to deploy your project.",
        )

    # node_modules
    if dir_path.name == "node_modules":
        return (
            "be npm's modules directory",
            "Node's package manager (npm) can store a vast number of files in these folders. These typically don't have to be included with your project and can easily be recreated later.",
        )

    # Build directories
    if dir_path.name in ("build", "dist"):
        return (
            "contain past build files",
            "Build directories can contain a large number of past build outputs and are not typically necessary to deploy your project.",
        )

    # All good, keep it
    return None


def list_files(
    proj: rio.cli.project.RioProject,
    dir_path: Path,
) -> Iterable[Path]:
    """
    Recursively yield all files in the given directory, ignoring any files that
    are ignored by the project.

    Any directories that should likely be excluded are ignored, unless
    explicitly listed in an exception in the `.rioignore` file.

    Interacts with the terminal.

    All yielded paths are absolute.
    """
    assert dir_path.exists(), dir_path
    assert dir_path.is_dir(), dir_path

    dir_path = dir_path.resolve()

    for path in dir_path.iterdir():
        # Ignore files that are ignored by the project
        if proj.ignores.is_path_ignored(path):
            continue

        # If this is a file, yield it
        if path.is_file():
            yield path
            continue

        # Is this a directory that the user likely doesn't want to include?
        exclude_reason = should_directory_likely_be_excluded(path)
        if (
            exclude_reason is not None
            and not proj.ignores.is_explicitly_included(path)
        ):
            appears_to, explanation = exclude_reason
            rel_path = path.relative_to(proj.project_directory)
            warning(
                f'Excluding "{rel_path}". This directory appears to {appears_to}.'
            )
            warning(explanation)
            warning(
                f'If you do want to include it after all, add the following to your ".rioignore" file:'
            )
            warning(f"!{rel_path}")
            print()

            # Explicitly ignore this directory
            proj.rioignore_additions.extend(
                [
                    f"# Automatically excluded by Rio",
                    f"# This directory appears to {appears_to}",
                    f"/{rel_path}",
                    "",
                ]
            )
            continue

        # Recurse
        yield from list_files(proj, path)


def pack_up_project(
    proj: rio.cli.project.RioProject,
    archive_path: Path,
) -> int:
    """
    Compresses all files in the project into an archive, displaying progress,
    and interacting with the terminal in general.

    Returns the size of the uncompressed files in bytes.
    """

    # Find all files which are part of the project
    print("Scanning project")
    project_directory = proj.project_directory.resolve()
    files = set(list_files(proj, project_directory))

    # Make sure essential files are included
    essential_files = {
        project_directory / "rio.toml",
    }

    missing_files = essential_files - files

    if missing_files:
        raise NotImplementedError(
            "TODO: Ask the user whether these files should be included"
        )

    # Gather all files into a single archive
    #
    # Randomize the file order to ensure that the progress is somewhat uniform.
    # Hard drives hate him.
    print("Creating app package")
    files = list(files)
    random.shuffle(files)
    total_size = 0

    with revel.ProgressBar() as bar:
        with tarfile.open(archive_path, "w:xz") as tar:
            for ii, file_path in enumerate(files):
                bar.progress = ii / len(files)

                # Add the file to the tarball
                relative_path = file_path.relative_to(project_directory)
                tar.add(file_path, arcname=relative_path)

                # Add the file size to the total
                total_size += file_path.stat().st_size

    return total_size


async def create_or_update_app(
    api: RioApi,
    proj: rio.cli.project.RioProject,
) -> None:
    """
    Uploads the given archive file to the cloud, creating a new deployment.
    """
    # Get an app name
    try:
        name = proj.deploy_name
    except KeyError:
        print(
            "What should your app be called? This name will be used as part of the URL."
        )
        print(
            'For example, if you name your app "my-app", it will be deployed at `https://rio.dev/.../my-app`.'
        )

        name = input("App name: ")

        allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789-"
        normalized = re.sub("[^" + allowed_chars + "]", "-", name.lower())
        normalized = re.sub("-+", "-", normalized)

    # Make sure the user is logged in
    # TODO

    # Pack up the project
    print_chapter("Packaging project")
    with tempfile.TemporaryDirectory() as tmp_dir:
        assert Path(tmp_dir).exists(), tmp_dir
        archive_path = Path(tmp_dir) / "packed-project.tar.xz"
        uncompressed_size_in_bytes = pack_up_project(proj, archive_path)
        compressed_size_in_bytes = archive_path.stat().st_size

        print(
            f"Compressed size: {compressed_size_in_bytes / 1024 / 1024:.2f} MiB"
        )
        print(
            f"Uncompressed size: {uncompressed_size_in_bytes / 1024 / 1024:.2f} MiB"
        )
        print(
            f"Compression ratio: {uncompressed_size_in_bytes / compressed_size_in_bytes:.2f}x"
        )

    # Make sure the user has the ability to create this app
    # TODO:
    # - # of apps
    # - compressed size
    # - uncompressed size

    # Create the app
    await api.create_app(
        name=app_name,
        packed_app=archive_path.open("rb"),
        realm=realm,
        start=start,
    )


async def main():
    with rio.cli.project.RioProject.try_locate_and_load() as proj:
        async with rio.cli.cli_instance.CliInstance() as cli:
            await create_or_update_app(None, proj)


if __name__ == "__main__":
    asyncio.run(main())
