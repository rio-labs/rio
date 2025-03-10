import logging

from .. import project_config

_logger = logging.getLogger(__name__)


import os
import typing as t
from pathlib import Path

import introspection
import revel
from revel import *  # type: ignore

import rio.global_state
import rio.snippets

from . import project_setup, run_project

__all__ = [
    "app",
]

revel.GLOBAL_STYLES.add_alias("primary", ["cyan"])
revel.GLOBAL_STYLES.add_alias("bg-primary", ["bg-cyan"])

app = revel.App(
    nicename="Rio",
    command_name="rio",
    summary="An easy to use, web & app framework for Python",
    details="""
Rio is a framework for building reactive apps and websites in Python. It's
designed to be easy to use, and to get out of your way as much as possible.

This is the command line interface for Rio. You can use it to easily create new
projects, run them, and more.
""",
    version=rio.__version__,
)


@app.command(
    aliases={"init", "create"},
    summary="Create a new Rio project",
    details="""
The `new` command creates a new directory and populates it with the files needed
to start a new Rio project. You can optionally specify a template, in which case
the files from that template will be copied into the new project, allowing you
hit the ground running.
""",
    parameters=[
        revel.Parameter(
            "nicename",
            summary="Human-readable name for the new project",
            prompt="What should the project be called?",
        ),
        revel.Parameter(
            "type",
            summary="Whether to create a website or an app",
        ),
        revel.Parameter(
            "template",
            summary="Template to use for the new project",
        ),
    ],
)
def new(
    nicename: str,
    *,
    # Website is listed first to make it the default
    type: t.Literal["website", "app"],
    template: rio.snippets.AvailableTemplatesLiteral,
) -> None:
    project_setup.create_project(
        raw_name=nicename,
        type=type,
        template_name=template,
        target_parent_directory=Path.cwd(),
        # The Rio website instantiates the sample projects and displays them as
        # live examples. Live examples differ slightly from the regular
        # templates. Let the outside world switch between the two modes, without
        # exposing a visible switch for it.
        as_live_example=os.environ.get("RIO_AS_LIVE_EXAMPLE") == "1",
    )


@app.command(
    summary="Run the current project",
    parameters=[
        revel.Parameter(
            "release",
            summary="Switches between release and debug mode",
        ),
        revel.Parameter(
            "port",
            summary="Port to run the HTTP server on",
        ),
        revel.Parameter(
            "public",
            summary="Whether the app should be available on the local network, rather than just the local device",
        ),
        revel.Parameter(
            "quiet",
            summary="Suppresses HTTP logs and other noise",
        ),
        revel.Parameter(
            "base_url",
            summary="The URL the app is hosted at",
        ),
    ],
    details="""
The `run` command runs the current project for debugging. If your project is a
website, it will be hosted on a local HTTP server, and you can view it in your
browser. If the project is a app, it will be displayed in a window instead.

Rio will constantly watch your project for changes, and automatically reload
the app or website when it detects a change. This makes it easy to iterate on
your project without having to manually restart it.

The `port` and `public` options are ignored if the project is an app, since
they only make sense for websites.

The base URL is where your app is hosted at, as seen from the client. So if the
user needs to type `https://example.com/my-app/` to see the app, this will be
`https://example.com/my-app/`. This is useful if you're hosting the app at a
sub-path of your domain, so that Rio can generate correct URLs for internal
assets and API calls. If you don't specify this, Rio assumes the app is hosted
at the root of your server. **This option is experimental. Please report any
issues you encounter. Even minor releases may change the behavior of this option
.**
""",
)
def run(
    *,
    release: bool = False,
    port: int | None = None,
    public: bool = False,
    quiet: bool = True,
    base_url: str | None = None,
) -> None:
    rio.global_state.launched_via_rio_run = True

    with project_config.RioProjectConfig.load_or_create_interactively() as proj:
        # Some options only make sense for websites
        if proj.app_type == "app":
            if port is not None:
                port = None
                warning(
                    "Ignoring the `port` option, since this project is not a website"
                )

            if public:
                public = False
                warning(
                    "Ignoring the `public` option, since this project is not a website"
                )

            if base_url is not None:
                base_url = None
                warning(
                    "Ignoring the `base-url` option, since this project is not a website"
                )

        # Parse the base URL
        if base_url is None:
            parsed_base_url = None
        else:
            try:
                parsed_base_url = rio.URL(base_url)
            except ValueError:
                fatal(f"The base-URL is not a valid URL: {base_url}")

            # If the URL is missing a protocol, yarl doesn't consider it
            # absolute. Perform a separate check for this so that the error
            # message makes more sense.
            if parsed_base_url.scheme not in ("http", "https"):
                fatal(
                    "Please provide a base URL that starts with either `http://` or `https://`."
                )

            # The URL must be absolute
            if not parsed_base_url.is_absolute():
                fatal("The base URL must be absolute.")

            # The URL must not contain a query or fragment
            if parsed_base_url.query:
                fatal("The base URL cannot contain query parameters.")

            if parsed_base_url.fragment:
                fatal("The base URL cannot contain a fragment.")

        # Running a project comes with considerable complexity. All of that is
        # crammed into classes.
        arbiter = run_project.Arbiter(
            proj=proj,
            port=port,
            public=public,
            quiet=quiet,
            debug_mode=not release,
            run_in_window=proj.app_type == "app",
            base_url=parsed_base_url,
        )
        arbiter.run()


@app.command(
    summary="Add a page or component to the project",
    parameters=[
        revel.Parameter(
            "what",
            summary="Whether to add a `page` or a `component`",
        ),
        revel.Parameter(
            "name",
            summary="The name of the new page or component",
        ),
    ],
    details="""
The `add` command adds a new page or component to your project. A python file
containing some template code will be created in the `pages` or `components`
folder of your project.
""",
)
def add(what: t.Literal["page", "component"], /, name: str) -> None:
    with project_config.RioProjectConfig.try_locate_and_load() as proj:
        try:
            module_path = proj.find_app_main_module_path()
        except FileNotFoundError as error:
            fatal(str(error))

        if not module_path.is_dir():
            fatal(
                f"Cannot add {what}s to a single-file project. Please convert"
                f" your project into a package."
            )

        # Make sure the `pages` or `components` folder exists
        folder_path = module_path / (what + "s")
        folder_path.mkdir(exist_ok=True)

        # Create the new file
        title_name = name.strip().replace("_", " ").replace("-", " ").title()
        name = name.strip().replace(" ", "_")
        class_name = introspection.convert_case(name, "pascal")
        url_segment = introspection.convert_case(name, "kebab")

        file_name = introspection.convert_case(name, "snake")
        file_path = folder_path / (file_name + ".py")

        if file_path.exists():
            fatal(f"File {file_path.relative_to(module_path)} already exists")

        # Write the file content
        if what == "page":
            file_path.write_text(
                f"""from __future__ import annotations

import typing as t

import rio

from .. import components as comps


@rio.page(
    name={title_name!r},
    url_segment={url_segment!r},
)
class {class_name}(rio.Component):
    def build(self) -> rio.Component:
        return rio.Markdown(
            '''
## This is a Sample Page

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.
            '''
        )
"""
            )
        else:
            file_path.write_text(
                f"""from __future__ import annotations

from dataclasses import KW_ONLY, field
import typing as t

import rio

from .. import components as comps


class {class_name}(rio.Component):
    example_state: str = "For demonstration purposes"

    def build(self) -> rio.Component:
        return rio.Text(self.example_state)
"""
            )

        # Import the module in the __init__.py
        #
        # For pages, only do this if the file already exists. When using
        # automatic page detection, no `__init__.py` file is used, and indeed
        # adding one is confusing Rio.
        init_py_path = file_path.with_name("__init__.py")

        try:
            init_py_code = init_py_path.read_text(encoding="utf8")
        except FileNotFoundError:
            init_py_code = None

        if what == "component" or init_py_code is not None:
            if init_py_code is None:
                init_py_code = ""
            else:
                init_py_code = init_py_code.rstrip()

            init_py_code += f"\nfrom .{file_name} import {class_name}\n"
            init_py_path.write_text(init_py_code, encoding="utf8")

        # Done. Tell the user
        success(
            f"New {what} created at {file_path.relative_to(proj.project_directory)}"
        )
