import io
import re
import shutil
import string
from pathlib import Path
from typing import *  # type: ignore

import introspection
import isort
import revel
from revel import fatal, print, success

import rio.cli
import rio.snippets

__all__ = [
    "create_project",
]


def class_name_from_snippet(snip: rio.snippets.Snippet) -> str:
    """
    Given a file name, determine the name of the class that is defined in it.

    e.g. `sample_component.py` -> `SampleComponent`
    """
    assert snip.name.endswith(".py"), snip.name

    parts = snip.name[:-3].split("_")
    return "".join(part.capitalize() for part in parts)


def write_init_file(fil: IO, snippets: Iterable[rio.snippets.Snippet]) -> None:
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
    out: TextIO,
    *,
    raw_name: str,
    project_type: Literal["app", "website"],
    components: List[rio.snippets.Snippet],
    pages: List[rio.snippets.Snippet],
    homepage_snippet: rio.snippets.Snippet,
    root_init_snippet: rio.snippets.Snippet,
    on_app_start: str | None = None,
    default_attachments: list[str] | None = None,
) -> None:
    """
    Generate the `__init__.py` file for the main module of the project.
    """
    assert len(pages) > 0, pages

    # If a page is called `root_page.py`, it will be used as the root component
    root_page_snippet: rio.snippets.Snippet | None = None

    for page in pages:
        if page.name == "root_page.py":
            root_page_snippet = page
            break

    # Ensure the homepage_snippet is the first in the pages list
    if pages[0] != homepage_snippet:
        pages = [homepage_snippet] + [
            page for page in pages if page != homepage_snippet
        ]

    # Prepare the different pages
    page_strings = []
    for snip in pages:
        page_component_name = class_name_from_snippet(snip)

        # Don't add the root page to the list of pages
        if snip is root_page_snippet:
            continue

        # What's the URL segment for this page?
        if snip is homepage_snippet:
            url_segment = ""
            page_nicename = "Home"
        else:
            assert snip.name.endswith(".py"), snip.name
            url_segment = snip.name[:-3].replace("_", "-").lower()
            page_nicename = page_component_name

        page_strings.append(
            f"""
        rio.Page(
            name="{page_nicename}",
            page_url={url_segment!r},
            build=pages.{page_component_name},
        ),"""
        )

    page_string = "\n".join(page_strings)

    # Prepare the default attachments
    if default_attachments is None:
        default_attachment_string = ""
    else:
        default_attachment_string = (
            f"\n    default_attachments=[{', '.join(default_attachments)}],"
        )

    # Imports
    default_theme = rio.Theme.from_colors()
    buffer = io.StringIO()

    buffer.write(
        f"""
from __future__ import annotations

from pathlib import Path
from typing import *  # type: ignore

import rio

from . import pages
from . import components as comps
    """.strip()
    )

    # Additional imports
    try:
        additional_imports = root_init_snippet.get_section("additional-imports")
    except KeyError:
        needs_isort = False
    else:
        buffer.write("\n")
        buffer.write(additional_imports)
        buffer.write("\n\n")
        needs_isort = True

    # Additional code
    try:
        additional_code = root_init_snippet.get_section("additional-code")
    except KeyError:
        pass
    else:
        buffer.write("\n")
        buffer.write(additional_code)
        buffer.write("\n\n")

    # Theme & App generation
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
    primary_color=rio.Color.from_hex("{default_theme.primary_color.hex}"),
    secondary_color=rio.Color.from_hex("{default_theme.secondary_color.hex}"),
    light=True,
)


# Create the Rio app
app = rio.App(
    name={raw_name!r},
    pages=[{page_string}
    ],{default_attachment_string}
"""
    )

    # Some parameters are optional
    if on_app_start is not None:
        buffer.write(
            f"    # This function will be called once the app is ready.\n"
            f"    #\n"
            f"    # `rio run` will also call it again each time the app is reloaded.\n"
            f"    on_app_start={on_app_start},\n"
        )

    if root_init_snippet is not None:
        buffer.write(
            "    # You can optionally provide a root component for the app. By default,\n"
            "    # a simple `rio.PageView` is used. By providing your own component, you\n"
            "    # can create components which stay put while the user navigates between\n"
            "    # pages, such as a navigation bar or footer.\n"
            "    #\n"
            "    # When you do this, make sure your component contains a `rio.PageView`\n"
            "    # so the currently active page is still visible.\n"
            "    build=pages.RootPage,\n"
        )

    buffer.write("    theme=theme,\n")
    buffer.write('    assets_dir=Path(__file__).parent / "assets",\n')
    buffer.write(")\n\n")

    # Due to imports coming from different sources they're often not sorted.
    # -> Apply `isort`
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
    out: TextIO,
    raw_name: str,
    template: rio.snippets.ProjectTemplate,
) -> None:
    out.write(
        f"""# {raw_name}

This is a placeholder README for your project. Use it to describe what your
project is about, to give new users a quick overview of what they can expect.

_{raw_name.capitalize()}_ was created using [Rio](http://rio.dev/), an easy to
use app & website framework for Python._
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
    out: TextIO,
    snip: rio.snippets.Snippet,
) -> None:
    """
    Writes the Python file containing a component or page to the given file.
    """
    # Common imports
    buffer = io.StringIO()

    buffer.write(
        f"""from __future__ import annotations

from dataclasses import KW_ONLY, field
from typing import *  # type: ignore

import rio

from .. import components as comps

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
    type: Literal["app", "website"],
    template_name: rio.snippets.AvailableTemplatesLiteral,
) -> None:
    """
    Create a new project with the given name. This will directly interact with
    the terminal, asking for input and printing output.
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
        assert False, f"Received invalid template name `{template_name}`. This shouldn't be possible if the types are correct."

    # Create the target directory
    project_dir = Path.cwd() / dashed_name
    project_dir.mkdir(parents=True, exist_ok=True)

    # If the project directory already exists it must be empty
    if any(project_dir.iterdir()):
        fatal(
            f"The project directory `{project_dir}` already exists and is not empty"
        )

    # Generate /rio.toml
    with open(project_dir / "rio.toml", "w", encoding="utf-8") as f:
        f.write("# This is the configuration file for Rio,\n")
        f.write("# an easy to use app & web framework for Python.\n")
        f.write("\n")
        f.write(f"[app]\n")
        f.write(f'app_type = "{type}"  # This is either "website" or "app"\n')
        f.write(
            f'main_module = "{module_name}"  # The name of your Python module\n'
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
            write_component_file(f, snip)

    # Generate pages/*.py
    for snip in template.page_snippets:
        target_path = pages_dir / snip.name

        with target_path.open("w", encoding="utf-8") as f:
            write_component_file(f, snip)

    # Generate /*.py
    for snip in template.other_python_files:
        source_string = snip.stripped_code()
        target_path = main_module_dir / snip.name

        with target_path.open("w", encoding="utf-8") as f:
            f.write(source_string)

    # Find the main page
    homepage_snippet = template.homepage_snippet

    # Generate /project/__init__.py
    with open(main_module_dir / "__init__.py", "w", encoding="utf-8") as fil:
        generate_root_init(
            out=fil,
            raw_name=raw_name,
            project_type=type,
            components=template.component_snippets,
            pages=template.page_snippets,
            homepage_snippet=homepage_snippet,
            root_init_snippet=template.root_init_snippet,
            on_app_start=template.on_app_start,
            default_attachments=template.default_attachments,
        )

    # Generate /project/components/__init__.py
    with open(
        main_module_dir / "components" / "__init__.py", "w", encoding="utf-8"
    ) as f:
        write_init_file(f, template.component_snippets)

    # Generate /project/pages/__init__.py
    with open(
        main_module_dir / "pages" / "__init__.py", "w", encoding="utf-8"
    ) as f:
        write_init_file(f, template.page_snippets)

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
sys.path.insert(0, str(Path(__file__).parent.parent))


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
    success(f"The project has been created!")
    success(f"You can find it at `{project_dir.resolve()}`")
    print()
    print(f"To see your new project in action, run the following commands:")
    print()
    print(f"[dim]>[/] cd {revel.shell_escape(project_dir.resolve())}")

    if template.dependencies:
        print(
            f"[dim]>[/] python -m pip install -r requirements.txt  [bold]# Don't forget to install dependencies![/]"
        )

    print(f"[dim]>[/] rio run")
