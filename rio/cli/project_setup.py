import io
import re
import shutil
import string
import typing as t
from pathlib import Path

import introspection
import isort
import revel
from revel import fatal, print, success

import rio.cli
import rio.snippets

from .. import project_config

__all__ = [
    "create_project",
]


def class_name_from_snippet(snip: rio.snippets.Snippet) -> str:
    """
    Given a file name, determine the name of the class that is defined in it.

    e.g. `my_component.py` -> `MyComponent`
    """
    assert snip.name.endswith(".py"), snip.name

    parts = snip.name[:-3].split("_")
    return "".join(part.capitalize() for part in parts)


def write_init_file(
    fil: t.IO, snippets: t.Iterable[rio.snippets.Snippet]
) -> None:
    """
    Write an `__init__.py` file that imports all of the snippets.

    e.g. if told to import snippets `foo.py` and `bar.py`, it will write:

    ```
    from .foo import Foo
    from .bar import Bar
    ```
    """
    for snippet in snippets:
        assert snippet.name.endswith(".py"), snippet.name
        module_name = snippet.name[:-3]
        class_name = class_name_from_snippet(snippet)
        fil.write(f"from .{module_name} import {class_name}\n")


def generate_root_init(
    out: t.TextIO,
    *,
    raw_name: str,
    project_type: t.Literal["app", "website"],
    template: rio.snippets.ProjectTemplate,
    as_live_example: bool,
) -> None:
    """
    Generate the `__init__.py` file for the main module of the project.
    """
    assert len(template.page_snippets) > 0, template.page_snippets

    # Imports
    default_theme = rio.Theme.from_colors()
    buffer = io.StringIO()

    buffer.write(
        """
from __future__ import annotations

from pathlib import Path
import typing as t

import rio

from . import components as comps
    """.strip()
    )

    # Additional imports
    try:
        additional_imports = template.root_init_snippet.get_section(
            "additional-imports"
        )
    except KeyError:
        needs_isort = False
    else:
        buffer.write("\n")
        buffer.write(additional_imports)
        buffer.write("\n")
        needs_isort = True

    buffer.write("\n\n")

    # Additional code
    try:
        additional_code = template.root_init_snippet.get_section(
            "additional-code"
        )
    except KeyError:
        pass
    else:
        buffer.write("\n")
        buffer.write(additional_code)
        buffer.write("\n\n")

    # If this is a live example, the template may optionally provide additional
    # code.
    #
    # If this is the case, the code will provide a function called
    # `on_demo_session_start`, which must be used instead of the regular session
    # start. This allows the demo code to clear the session for each user.
    #
    # This supersedes any previous `on_session_start` function - the demo code
    # can call that function itself if it needs to.
    on_session_start_function_name: str | None = template.on_session_start

    if as_live_example:
        try:
            additional_demo_code = template.root_init_snippet.get_section(
                "additional-demo-code"
            )
        except KeyError:
            pass
        else:
            buffer.write("\n")
            buffer.write(additional_demo_code)
            buffer.write("\n\n")

            on_session_start_function_name = "on_demo_session_start"

    # Theme generation if not provided by the template
    if template.theme is None:
        buffer.write(
            f"""
# Define a theme for Rio to use.
#
# You can modify the colors here to adapt the appearance of your app or website.
# The most important parameters are listed, but more are available! You can find
# them all in the docs
#
# https://rio.dev/docs/api/theme
theme = rio.Theme.from_colors(
    primary_color=rio.Color.from_hex("{default_theme.primary_color.hexa}"),
    secondary_color=rio.Color.from_hex("{default_theme.secondary_color.hexa}"),
    mode="light",
)


""".lstrip()
        )

    # App generation
    buffer.write("# Create the Rio app\n")
    buffer.write("app = rio.App(\n")

    # In live demos, use the template name as app name
    if as_live_example:
        buffer.write(f"    name={template.name!r},\n")
    else:
        buffer.write(f"    name={raw_name!r},\n")

    # Optional: `default_attachments`
    if template.default_attachments is not None:
        buffer.write(
            f"    default_attachments=[{', '.join(template.default_attachments)}],\n"
        )

    # Optional: `on_app_start`
    if template.on_app_start is not None:
        buffer.write(
            f"    # This function will be called once the app is ready.\n"
            f"    #\n"
            f"    # `rio run` will also call it again each time the app is reloaded.\n"
            f"    on_app_start={template.on_app_start},\n"
        )

    # Optional: `on_session_start`
    if on_session_start_function_name is not None:
        if project_type == "app":
            buffer.write(
                "    # This function will be called when a user opens the app. Its\n"
                "    # mostly used for web apps, where each user starts a new\n"
                "    # session when they connect.\n"
            )
        else:
            buffer.write(
                "    # This function will be called each time a user connects\n"
            )

        buffer.write(
            f"    on_session_start={on_session_start_function_name},\n"
        )

    # Optional: `root_component`
    if template.root_component is not None:
        buffer.write(
            f"    # You can optionally provide a root component for the app. By default,\n"
            f"    # Rio's default navigation is used. By providing your own component, you\n"
            f"    # can create components which stay put while the user navigates between\n"
            f"    # pages, such as a navigation bar or footer.\n"
            f"    #\n"
            f"    # When you do this, make sure your component contains a `rio.PageView`\n"
            f"    # so the currently active page is still visible.\n"
            f"    build=comps.{template.root_component},\n"
        )

    # Pass in the theme
    if template.theme is not None:
        buffer.write(
            f"    # You can also provide a custom theme for the app. This theme will\n"
            f"    # override Rio's default.\n"
            f"    theme={template.theme},\n"
        )
    elif as_live_example:
        # In live examples, enable both light and dark mode
        buffer.write("    theme=rio.Theme.pair_from_colors(),\n")
    else:
        buffer.write("    theme=theme,\n")

    # Configure the assets directory
    buffer.write('    assets_dir=Path(__file__).parent / "assets",\n')
    buffer.write(")\n\n")

    # Due to imports coming from different sources they're often not sorted. Fix
    # that now.
    if needs_isort:
        formatted_code = isort.code(buffer.getvalue())
        out.write(formatted_code)
    else:
        out.write(buffer.getvalue())


def strip_invalid_filename_characters(name: str) -> str:
    """
    Given a name, strip any characters that are not allowed in a filename.
    """
    return re.sub(r'[<>:"/\\|?*]', "", name)


def derive_module_name(raw_name: str) -> str:
    """
    Given an arbitrary string, derive similar and valid all_lower Python module
    identifier from it.
    """
    # Convert to lower_case
    name = introspection.convert_case(raw_name, "snake")

    # Strip any invalid characters
    name = "".join(c for c in name if c.isidentifier() or c in string.digits)

    # Since modules are written to files, the name also has to be a valid file
    # name
    name = strip_invalid_filename_characters(name)

    # Identifiers cannot start with a digit
    while name and name[0].isdigit():
        name = name[1:]

    # This could've resulted in an empty string
    if not name:
        name = "rio_app"

    # Done
    return name


def generate_readme(
    out: t.TextIO,
    raw_name: str,
    template: rio.snippets.ProjectTemplate,
) -> None:
    out.write(
        f"""# {raw_name}

This is a placeholder README for your project. Use it to describe what your
project is about, to give new users a quick overview of what they can expect.

_{raw_name.capitalize()}_ was created using [Rio](https://rio.dev/), an easy to
use app & website framework for Python.
"""
    )

    # Include the template's README
    if template.name != "Empty":
        out.write(
            f"""
This project is based on the `{template.name}` template.

## {template.name}

{template.description_markdown_source}
"""
        )


def write_component_file(
    out: t.TextIO,
    snip: rio.snippets.Snippet,
    import_depth: int,
) -> None:
    """
    Writes the Python file containing a component or page to the given file.
    """
    # Common imports
    buffer = io.StringIO()

    dots = "." * (import_depth + 1)

    buffer.write(
        f"""from __future__ import annotations

from dataclasses import KW_ONLY, field
import typing as t

import rio

from {dots} import components as comps

"""
    )

    # Additional, user-defined imports
    try:
        additional_imports = snip.get_section("additional-imports")
    except KeyError:
        needs_isort = False
    else:
        buffer.write(additional_imports)
        buffer.write("\n")
        needs_isort = True

    # The component proper
    buffer.write(snip.get_section("component"))

    # Due to imports coming from different sources they're often not sorted.
    # -> Apply `isort`
    if needs_isort:
        formatted_code = isort.code(buffer.getvalue())
        out.write(formatted_code)
    else:
        out.write(buffer.getvalue())


def generate_dependencies_file(
    project_dir: Path, dependencies: dict[str, str]
) -> None:
    """
    Writes a `requirements.txt` file with the given dependencies. Does nothing
    if there are no dependencies.
    """
    # Anything to do?
    if not dependencies:
        return

    # requirements.txt
    with open(project_dir / "requirements.txt", "w", encoding="utf-8") as out:
        for package, version_specifier in dependencies.items():
            out.write(f"{package}{version_specifier}\n")


def create_project(
    *,
    raw_name: str,
    type: t.Literal["app", "website"],
    template_name: rio.snippets.AvailableTemplatesLiteral,
    target_parent_directory: Path,
    as_live_example: bool = False,
) -> None:
    """
    Create a new project with the given name. This will directly interact with
    the terminal, asking for input and printing output.

    ## Parameters

    `as_live_example`: This makes some changes to the created project to make it
        more suitable for live examples. For example, additional code can be run
        on session start to clean up the app for every user.
    """

    # Derive a valid module name
    module_name = derive_module_name(raw_name)

    # The project directory is called the same, but in kebab-case
    dashed_name = module_name.replace("_", "-")

    # Find the template
    for template in rio.snippets.get_project_templates(include_empty=True):
        if template.name == template_name:
            break
    else:
        assert False, (
            f"Received invalid template name `{template_name}`. This shouldn't be possible if the types are correct."
        )

    # Create the target directory
    project_dir = target_parent_directory / dashed_name
    project_dir.mkdir(parents=True, exist_ok=True)

    # If the project directory already exists it must be empty
    if any(project_dir.iterdir()):
        fatal(
            f"The project directory `{project_dir}` already exists and is not empty"
        )

    # Generate /rio.toml
    project_config.RioProjectConfig.create(
        project_dir / "rio.toml",
        main_module=module_name,
        project_type=type,
    )

    # Create the main module and its subdirectories
    main_module_dir = project_dir / module_name
    assets_dir = main_module_dir / "assets"
    components_dir = main_module_dir / "components"
    pages_dir = main_module_dir / "pages"

    main_module_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir()
    components_dir.mkdir()
    pages_dir.mkdir()

    # Generate /assets/*
    for snip in template.asset_snippets:
        source_path = snip.file_path
        target_path = assets_dir / source_path.name
        shutil.copyfile(source_path, target_path)

    # Generate /components/*.py
    for snip in template.component_snippets:
        target_path = components_dir / snip.name

        with target_path.open("w", encoding="utf-8") as f:
            write_component_file(
                f,
                snip,
                import_depth=1,
            )

    # Generate pages/*.py
    #
    # Pages are more complicated, because they may be placed in subdirectories.
    # Get this page's relative path.
    template_pages_dir = template.root_init_snippet.file_path.parent / "pages"

    for snip in template.page_snippets:
        rel_path = snip.file_path.relative_to(template_pages_dir)
        target_path = pages_dir / rel_path

        target_path.parent.mkdir(parents=True, exist_ok=True)

        with target_path.open("w", encoding="utf-8") as f:
            write_component_file(
                f,
                snip,
                import_depth=len(rel_path.parts),
            )

    # Generate /*.py
    for snip in template.other_python_files:
        source_string = snip.stripped_code()
        target_path = main_module_dir / snip.name

        with target_path.open("w", encoding="utf-8") as f:
            f.write(source_string)

    # Generate /project/__init__.py
    with open(main_module_dir / "__init__.py", "w", encoding="utf-8") as fil:
        generate_root_init(
            out=fil,
            raw_name=raw_name,
            project_type=type,
            template=template,
            as_live_example=as_live_example,
        )

    # Generate /project/components/__init__.py
    with open(
        main_module_dir / "components" / "__init__.py", "w", encoding="utf-8"
    ) as f:
        write_init_file(f, template.component_snippets)

    # Generate a file specifying all dependencies, if there are any
    generate_dependencies_file(project_dir, template.dependencies)

    # Generate README.md
    with open(project_dir / "README.md", "w", encoding="utf-8") as f:
        generate_readme(f, raw_name, template)

    # Applications require a `__main__.py` as well
    if type == "app":
        with open(main_module_dir / "__main__.py", "w", encoding="utf-8") as f:
            f.write(
                f"""
# Make sure the project is in the Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).absolute().parent.parent))


# Import the main module
import {module_name}

# Run the app
{module_name}.app.run_in_window()
"""
            )

    # Report success
    #
    # TODO: Other tools like poetry!? Add a command to activate the venv?
    print()
    success("The project has been created!")
    success(f"You can find it at `{project_dir.resolve()}`")
    print()
    print("To see your new project in action, run the following commands:")
    print()
    print(f"[dim]>[/] cd {revel.shell_escape(project_dir.resolve())}")

    if template.dependencies:
        print(
            "[dim]>[/] python -m pip install -r requirements.txt  [bold]# Don't forget to install dependencies![/]"
        )

    print("[dim]>[/] rio run")
