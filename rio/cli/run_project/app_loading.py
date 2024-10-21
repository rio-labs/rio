import functools
import html
import os
import sys
import traceback
import types
import typing as t
from pathlib import Path

import path_imports
import revel

import rio
import rio.global_state
from rio import icon_registry

from ... import project_config
from .. import nice_traceback


class AppLoadError(Exception):
    pass


def traceback_frame_filter(frame: traceback.FrameSummary) -> bool:
    # Skip frames which are internal to rio
    rio_root = rio.__file__
    assert rio_root.endswith(os.sep + "__init__.py")
    rio_root = rio_root.removesuffix(os.sep + "__init__.py")

    return not frame.filename.startswith(rio_root)


def make_traceback_html(
    *,
    err: t.Union[str, BaseException],
    project_directory: Path,
) -> str:
    error_icon_svg = icon_registry.get_icon_svg("material/error")

    if isinstance(err, str):
        traceback_html = html.escape(err)
    else:
        traceback_html = nice_traceback.format_exception_html(
            err,
            relpath=project_directory,
            frame_filter=traceback_frame_filter,
        )

    return f"""
<div class="rio-traceback rio-dev-tools-background rio-switcheroo-neutral">
    <div class="rio-traceback-header">
        {error_icon_svg}
        <div>Couldn't load the app</div>
    </div>
    <div class="rio-traceback-message">
        Fix the issue below. The app will automatically reload once you save the
        file.
    </div>
    <div class="rio-traceback-traceback">{traceback_html}</div>
    <div class="rio-traceback-footer">
        Need help?
        <div class="rio-traceback-footer-links">
            <a class="rio-text-link" target="_blank" href="https://discord.gg/7ejXaPwhyH">Ask on Rio's Discord</a>
            <a class="rio-text-link" target="_blank" href="https://chatgpt.com">Ask ChatGPT</a>
            <a class="rio-text-link" target="_blank" href="https://rio.dev/docs?s=bf2">Read the docs</a>
        </div>
    </div>
</div>
"""


def make_error_message_component(
    err: t.Union[str, BaseException],
    project_directory: Path,
) -> rio.Component:
    html = make_traceback_html(
        err=err,
        project_directory=project_directory,
    )

    return rio.Html(
        html,
        align_x=0.5,
        align_y=0.2,
    )


def make_error_message_app(
    err: t.Union[str, BaseException],
    project_directory: Path,
    theme: rio.Theme | tuple[rio.Theme, rio.Theme],
) -> rio.App:
    """
    Creates an app that displays the given error message.
    """
    return rio.App(
        build=functools.partial(
            make_error_message_component, err, project_directory
        ),
        theme=theme,
    )


def import_app_module(
    proj: project_config.RioProjectConfig,
) -> types.ModuleType:
    """
    This can raise a variety of exceptions, since the module's code is
    evaluated.
    """
    # Purge the module from the module cache
    app_main_module = proj.app_main_module
    root_module, _, _ = app_main_module.partition(".")

    for module_name in list(sys.modules):
        if module_name.partition(".")[0] == root_module:
            del sys.modules[module_name]

    # Explicitly tell the app what the "main file" is, because otherwise it
    # would be detected incorrectly.
    rio.global_state.rio_run_app_module_path = proj.app_main_module_path

    # Now (re-)import the app module
    try:
        return path_imports.import_from_path(
            proj.app_main_module_path,
            app_main_module,
            # Newbies often don't organize their code as a single module, so to
            # guarantee that all their files can be imported, we'll add the
            # relevant directory to `sys.path`
            add_parent_directory_to_sys_path=True,
        )
    finally:
        rio.global_state.rio_run_app_module_path = None


def load_user_app(proj: project_config.RioProjectConfig) -> rio.App:
    """
    Load and return the user app. Raises `AppLoadError` if the app can't be
    loaded for whichever reason.
    """
    # Import the app module
    try:
        app_module = import_app_module(proj)
    except BaseException as err:
        revel.error(f"Could not import `{proj.app_main_module}`:")

        revel.print(
            nice_traceback.format_exception_revel(
                err,
                relpath=proj.project_directory,
                frame_filter=traceback_frame_filter,
            )
        )

        raise AppLoadError() from err

    # Find the variable holding the Rio app
    apps: list[tuple[str, rio.App]] = []
    for var_name, var in app_module.__dict__.items():
        if isinstance(var, rio.App):
            apps.append((var_name, var))

    if app_module.__file__ is None:
        main_file_reference = f"Your app's main file"
    else:
        main_file_reference = f"The file `{Path(app_module.__file__).relative_to(proj.project_directory)}`"

    if len(apps) == 0:
        raise AppLoadError(
            f"Cannot find your app. {main_file_reference} needs to to define a"
            f" variable that is a Rio app. Something like `app = rio.App(...)`"
        )

    if len(apps) > 1:
        variables_string = (
            "`" + "`, `".join(var_name for var_name, _ in apps) + "`"
        )
        raise AppLoadError(
            f"{main_file_reference} defines multiple Rio apps: {variables_string}. Please make sure there is exactly one."
        )

    return apps[0][1]
