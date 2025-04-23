import random
import tarfile
import tempfile
import typing as t
from datetime import datetime
from pathlib import Path

import revel
import rio_api_client.api.default.app_create_app_create_post
import rio_api_client.api.default.app_create_archive_app_create_archive_post
import rio_api_client.api.default.deployment_create_deployment_create_post
import rio_api_client.api.default.deployment_delete_deployment_delete_post
import rio_api_client.api.default.get_user_user_me_get
import rio_api_client.models
import rio_api_client.types

import rio.project_config


def _should_directory_likely_be_excluded(
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
            "Virtual environments contain a huge number of files which are typically created by `uv`, `venv`, `poetry`, `conda` or similar tools. These don't have to be included with your project and can easily be recreated later.",
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


def _list_files(
    proj: rio.project_config.RioProjectConfig,
    dir_path: Path,
) -> t.Iterable[Path]:
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
        if not proj.file_is_path_of_project(path):
            continue

        # If this is a file, yield it
        if path.is_file():
            yield path
            continue

        # Is this a directory that the user likely doesn't want to include?
        exclude_reason = _should_directory_likely_be_excluded(path)
        if (
            exclude_reason is not None
            and not proj.ignores.is_explicitly_included(path)
        ):
            appears_to, explanation = exclude_reason
            rel_path = path.relative_to(proj.project_directory)
            revel.warning(
                f'Excluding "{rel_path}". This directory appears to {appears_to}.'
            )
            revel.warning(explanation)
            revel.warning(
                f'If you do want to include it after all, add the following to your ".rioignore" file:'
            )
            revel.warning(f"!{rel_path}")
            revel.print()

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
        yield from _list_files(proj, path)


def _pack_up_project(
    proj: rio.project_config.RioProjectConfig,
    archive_path: Path,
) -> int:
    """
    Compresses all files in the project into an archive, displaying progress,
    and interacting with the terminal in general.

    Returns the size of the uncompressed files in bytes.
    """

    # Find all files which are part of the project
    revel.print("Scanning project")
    project_directory = proj.project_directory.resolve()
    files = set(_list_files(proj, project_directory))

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
    revel.print("Creating app package")
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


async def _get_or_create_app(
    client: rio_api_client.Client,
    proj: rio.project_config.RioProjectConfig,
) -> rio_api_client.models.UserApp:
    """
    Every app in the cloud has a unique ID. The first time a project is
    deployed, the app ID is created and stored in the `rio.toml`.

    This function gets the app corresponding to this project. If the project
    doesn't have an app yet, creates a new one.

    This function interacts directly with the terminal should user input be
    required.
    """
    app_id = proj.deployment_app_id

    # If no app ID is stored with the project, there obviously isn't an
    # associated app.
    if app_id is None:
        pass

    # If an app ID is stored, make sure that app indeed exists on the API, and
    # this user has access to it.
    else:
        user_response = (
            await rio_api_client.api.default.get_user_user_me_get.asyncio(
                client=client
            )
        )
        assert isinstance(
            user_response, rio_api_client.models.ResponseGetUser
        ), user_response

        for app in user_response.apps:
            if app.app_id == app_id:
                return app

    # No app ID was found, so create a new one
    project_nicename = (
        proj.project_directory.name.strip()
        .replace("-", " ")
        .replace("_", " ")
        .title()
    )

    app = await rio_api_client.api.default.app_create_app_create_post.asyncio(
        client=client,
        body=rio_api_client.models.RequestCreateApp(
            name=project_nicename,
        ),
    )

    # Return the fresh app
    assert isinstance(app, rio_api_client.models.UserApp), app
    return app


async def get_user(
    *,
    client: rio_api_client.Client,
) -> rio_api_client.models.ResponseGetUser:
    """
    Retrieves the currently logged in user from the API.
    """
    user_response = (
        await rio_api_client.api.default.get_user_user_me_get.asyncio(
            client=client
        )
    )
    assert isinstance(user_response, rio_api_client.models.ResponseGetUser), (
        "Expected a ResponseGetUser, but got: "
        f"{user_response.__class__.__name__}"
    )
    return user_response


async def start_app(
    *,
    client: rio_api_client.Client,
    proj: rio.project_config.RioProjectConfig,
    archive_id: str | t.Literal["latest"],
) -> None:
    """
    Deploys the app to the cloud, creating it if it doesn't exist yet.
    """
    # Get the app, creating a new one if the project isn't associated with any
    # yet.
    app = await _get_or_create_app(client, proj)

    # Which archive to use? If none is explicitly provided, find the latest one.
    if archive_id == "latest":
        app.archives.sort(
            key=lambda archive: datetime.fromisoformat(archive.created_at),
        )

        if not app.archives:
            raise NotImplementedError("TODO: The app has no archives yet")

        archive_id = app.archives[-1].id

    # Create a new deployment for this app
    await rio_api_client.api.default.deployment_create_deployment_create_post.asyncio(
        client=client,
        body=rio_api_client.models.RequestCreateDeployment(
            archive_id=archive_id,
        ),
    )


async def update_app(
    *,
    client: rio_api_client.Client,
    proj: rio.project_config.RioProjectConfig,
) -> None:
    """
    Sends the current project files to the cloud, as archive in the current app.
    """
    # Get the app, creating a new one if the project isn't associated with any
    # yet.
    app = await _get_or_create_app(client, proj)

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Pack up the project into a single archive
        archive_path = Path(tmp_dir) / "packed-project.tar.xz"
        uncompressed_size_in_bytes = _pack_up_project(proj, archive_path)
        compressed_size_in_bytes = archive_path.stat().st_size

        # TODO: Verify that the project isn't too big right here. While the
        # server will obviously also have to check this, it would be nice to
        # tell the user _before_ starting to transmit tons of data.

        # Upload the archive to the cloud
        await rio_api_client.api.default.app_create_archive_app_create_archive_post.asyncio(
            client=client,
            body=rio_api_client.models.BodyAppCreateArchiveAppCreateArchivePost(
                args=rio_api_client.models.RequestCreateAppArchive(
                    app_id=app.app_id,
                ),
                app_archive=rio_api_client.types.File(
                    payload=archive_path.open("rb"),
                    file_name=archive_path.name,
                    mime_type="application/x-xz",
                ),
            ),
        )


async def stop_app(
    *,
    client: rio_api_client.Client,
    deployment_id: str,
) -> None:
    """
    Stops one of the app's deployments.
    """
    # Stop the deployment
    await rio_api_client.api.default.deployment_delete_deployment_delete_post.asyncio(
        client=client,
        body=rio_api_client.models.RequestDeleteDeployment(
            deployment_id=deployment_id,
        ),
    )
