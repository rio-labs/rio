import functools
import html
import sys
import types
import typing as t
from pathlib import Path

import path_imports

import rio
import rio.app_server.fastapi_server
import rio.global_state

from ... import icon_registry, nice_traceback, project_config


class AppLoadError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)

    @property
    def message(self) -> str:
        return self.args[0]


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

    return rio.Webview(
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
        # Make sure to explicitly suppress any pages. If not passed, Rio will
        # attempt to auto-detect the pages, which aren't meant for the
        # placeholder app.
        pages=[],
        theme=theme,
    )


def modules_in_directory(project_path: Path) -> t.Iterable[str]:
    """
    Returns all currently loaded modules that reside in the given directory (or
    any subdirectory thereof). As a second condition, modules located inside of
    a virtual environment are not returned.

    The purpose of this is to yield all modules that belong to the user's
    project. This is the set of modules that makes sense to reload when the user
    makes a change.
    """
    # Resolve the path to avoid issues with symlinks
    project_path = project_path.resolve()

    # Walk all modules
    for name, module in list(sys.modules.items()):
        # Special case: Unloading Rio, while Rio is running is not that smart.
        #
        # Also make sure "__main__" isn't unloaded. This can happen because the
        # project is running as `rio run` (which makes rio "__main__") and if
        # rio is located in the project directory.
        if name in ("__main__", "rio") or name.startswith("rio."):
            continue

        # Where does the module live?
        #
        # This needs to take namespace packages into account, which don't have a
        # single path.
        module_paths: t.Iterable[object]

        try:
            module_paths = iter(module.__path__)
        except KeyError:
            # `__path__` is a weird iterable that executes code when you iterate
            # over it. This code crashes with a KeyError if the parent module
            # is missing from `sys.modules`.
            #
            # In such a case, the safe play is to reload the module. The
            # worst case scenario is that we'll reload a module that didn't need
            # to be reloaded, which is much better than *not* reloading a module
            # that should be.
            yield name
            continue
        except AttributeError:
            module_paths = [getattr(module, "__file__", None)]
        except TypeError:
            continue

        # If any path is inside of the process directory, yield the module
        for module_path in module_paths:
            # Get the path
            try:
                module_path = Path(module_path).resolve()  # type: ignore
            except TypeError:
                continue

            # If the module isn't inside of the project directory, skip it
            try:
                module_rel_path = module_path.relative_to(project_path)
            except ValueError:
                continue

            # If the module is unlikely to be related to this project, skip it
            if "site-packages" in module_rel_path.parts:
                continue

            # Yield the module
            yield name
            break


def import_app_module(
    proj: project_config.RioProjectConfig,
) -> types.ModuleType:
    """
    This function imports the app module, as specified by the user.

    The module will be freshly imported, even if it was already imported before.
    """
    # Purge all modules that belong to the project. While the main module name
    # is known, deleting only that isn't enough in all projects. In complex
    # project structures it can be useful to have the UI code live in a module
    # that is then just loaded into a top-level Python file.
    #
    # `modules_in_directory` returns an iterable that can still run code while
    # being iterated over. Some of that code attempts to access modules from
    # `sys.modules`. If we were to start deleting modules while the iterable is
    # still being generated, some of this code can fail because it can't find
    # its module. To avoid this, store everything in a list first, then walk
    # that list again.
    modules = list(modules_in_directory(proj.project_directory))

    for module_name in modules:
        del sys.modules[module_name]

    # Explicitly tell the app what the "main file" is, because otherwise it
    # would be detected incorrectly.
    app_main_module_path = proj.find_app_main_module_path()
    rio.global_state.rio_run_app_module_path = app_main_module_path

    # Now (re-)import the app module. There is no need to import all the other
    # modules here, since they'll be re-imported as needed by the app module.
    try:
        mod = path_imports.import_from_path(
            app_main_module_path,
            proj.app_main_module_name,
            import_parent_modules=True,
            # Newbies often don't organize their code as a single module, so to
            # guarantee that all their files can be imported, we'll add the
            # relevant directory to `sys.path`
            add_parent_directory_to_sys_path=True,
        )
        return mod

    finally:
        rio.global_state.rio_run_app_module_path = None


def load_user_app(
    proj: project_config.RioProjectConfig,
) -> rio.app_server.fastapi_server.FastapiServer:
    """
    Load and return the user's app. Raises `AppLoadError` if the app can't be
    loaded for whichever reason.

    The result is actually an app server, rather than just the app. This is done
    so the user can use `as_fastapi` on a Rio app and still use `rio run` to run
    it. If you actually need the app object itself, grab it from within the
    server.
    """
    # Import the app module
    try:
        app_module = import_app_module(proj)
    except FileNotFoundError as err:
        raise AppLoadError(
            f"Could not import `{proj.app_main_module_name}`: Module not found"
        )
    except ImportError as err:
        real_error = err.__cause__
        assert real_error is not None, err

        raise AppLoadError(
            f"Could not import `{proj.app_main_module_name}`: {real_error}"
        ) from real_error

    # Find the variable holding the Rio app.
    #
    # There are two cases here. Typically, there will be an instance of
    # `rio.App` somewhere. However, in order for users to be able to add custom
    # routes, there might also be a variable storing a `fastapi.FastAPI`, or, in
    # our case, Rio's subclass thereof. If that is present, prefer it over the
    # plain Rio app.
    as_fastapi_apps: list[
        tuple[str, rio.app_server.fastapi_server.FastapiServer]
    ] = []
    rio_apps: list[tuple[str, rio.App]] = []

    for var_name, var in app_module.__dict__.items():
        if isinstance(var, rio.app_server.fastapi_server.FastapiServer):
            as_fastapi_apps.append((var_name, var))

        elif isinstance(var, rio.App):
            rio_apps.append((var_name, var))

    # Prepare the main file name
    if app_module.__file__ is None:
        main_file_reference = f"Your app's main file"
    else:
        main_file_reference = f"The file `{Path(app_module.__file__).relative_to(proj.project_directory)}`"

    # Which type of app do we have?
    #
    # Case: FastAPI app
    if len(as_fastapi_apps) > 0:
        app_list = as_fastapi_apps
        app_server = as_fastapi_apps[0][1]
    # Case: Rio app
    elif len(rio_apps) > 0:
        app_list = rio_apps
        app_instance = rio_apps[0][1]
        app_server = app_instance.as_fastapi()
        assert isinstance(
            app_server, rio.app_server.fastapi_server.FastapiServer
        )
    # Case: No app
    else:
        raise AppLoadError(
            f"Cannot find your app. {main_file_reference} needs to to define a"
            f" variable that is a Rio app. Something like `app = rio.App(...)`"
        )

    # Make sure there was only one app to choose from, within the chosen
    # category
    if len(app_list) > 1:
        variables_string = (
            "`" + "`, `".join(var_name for var_name, _ in app_list) + "`"
        )
        raise AppLoadError(
            f"{main_file_reference} defines multiple Rio apps: {variables_string}. Please make sure there is exactly one."
        )

    return app_server
