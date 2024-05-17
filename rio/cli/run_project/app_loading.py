import functools
import html
import os
import sys
import traceback
import types
from pathlib import Path
from typing import *  # type: ignore

import revel

import rio
import rio.icon_registry

from .. import nice_traceback, project


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
    err: Union[str, BaseException],
    project_directory: Path,
) -> str:
    icon_registry = rio.icon_registry.IconRegistry.get_singleton()
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
<div>
    <div class="rio-traceback rio-debugger-background rio-switcheroo-neutral">
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
                <a class="rio-text-link" target="_blank" href="https://rio.dev/docs">Read the docs</a>
            </div>
        </div>
    </div>
</div>
"""


def make_error_message_component(
    err: Union[str, BaseException],
    project_directory: Path,
) -> rio.Component:
    html = make_traceback_html(
        err=err,
        project_directory=project_directory,
    )

    return rio.Html(html)


def make_error_message_app(
    err: Union[str, BaseException],
    project_directory: Path,
    theme: rio.Theme | Tuple[rio.Theme, rio.Theme],
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


def import_app_module(proj: project.RioProject) -> types.ModuleType:
    """
    Python's importing is bizarre. This function tries to hide all of that and
    imports the module, as specified by the user. This can raise a variety of
    exceptions, since the module's code is evaluated.
    """
    # Purge the module from the module cache
    app_main_module = proj.app_main_module
    root_module, _, _ = app_main_module.partition(".")

    for module_name in list(sys.modules):
        if module_name.partition(".")[0] == root_module:
            del sys.modules[module_name]

    # Now (re-)import the app module
    main_module_path = str(proj.module_path.parent)
    sys.path.append(main_module_path)

    try:
        return __import__(app_main_module)
    finally:
        sys.path.remove(main_module_path)


def load_user_app(proj: project.RioProject) -> rio.App:
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
            f"Cannot find your app. {main_file_reference} needs to to define a variable that is a Rio app. Something like `app = rio.App(...)`"
        )

    if len(apps) > 1:
        variables_string = (
            "`" + "`, `".join(var_name for var_name, _ in apps) + "`"
        )
        raise AppLoadError(
            f"{main_file_reference} defines multiple Rio apps: {variables_string}. Please make sure there is exactly one."
        )

    app = apps[0][1]

    # Explicitly set the asset directory because it can't reliably be
    # auto-detected
    module_path = proj.module_path
    if module_path.is_file():
        module_path = module_path.parent
    app.assets_dir = module_path / app._assets_dir

    # If runnWrap the app's `build` function so that it displays a nice traceback
    # in case of an error

    return app
