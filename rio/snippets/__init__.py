from __future__ import annotations

import copy
import functools
import json
import re
import typing as t
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import typing_extensions as te
import uniserde

from .. import utils

SECTION_PATTERN = re.compile(r" *#\s*<(\/?[\w-]+)>")


# Contains default values for the `meta.json` file
DEFAULT_META_DICT = {
    "dependencies": {},
    "rootComponent": None,
    "onAppStart": None,
    "onSessionStart": None,
    "defaultAttachments": None,
}


# All Available templates, including the empty template
#
# THE ORDER MATTERS. `revel` will display the options in the same order as they
# appear in the literal
AvailableTemplatesLiteral: te.TypeAlias = t.Literal[
    # Keep the empty template first
    "Empty",
    # Sort the remainder alphabetically
    "AI Chatbot",
    "Authentication",
    "Crypto Dashboard",
    "Multipage Website",
    "Simple CRUD",
    "Tic-Tac-Toe",
    "Todo App",
]


@dataclass
class _TemplateConfig(uniserde.Serde):
    """
    Model for parsing the JSON file which comes along with each project
    template.
    """

    # Allows displaying the templates in a structured way
    level: t.Literal["beginner", "intermediate", "advanced"]

    # Very short, one or two line description of the template
    summary: str

    # Any pypi packages this project depends on, in the same format as used by
    # `pip`.
    #
    # Example: `{"numpy": ">=1.21.0", "pandas": "^1.3.0"}`
    dependencies: dict[str, str]

    # Additional parameters to pass to the app instance
    root_component: str | None
    on_app_start: str | None
    on_session_start: str | None
    default_attachments: list[str] | None


@dataclass
class Snippet:
    # The group the snippet is in
    group: str

    # The name the snippet can be accessed with
    name: str

    # The path to the snippet file
    file_path: Path

    # For text snippets, this is the raw file contents. `None` for binary
    # snippets.
    raw_code: str | None

    @property
    def is_text_snippet(self) -> bool:
        return self.raw_code is not None

    @property
    def is_binary_snippet(self) -> bool:
        return not self.is_text_snippet

    @staticmethod
    def from_path(group: str, name: str, file_path: Path) -> Snippet:
        # Read the contents if it's a text snippet
        if file_path.suffix in (".txt", ".md", ".py", ".json"):
            raw_code = file_path.read_text(encoding="utf-8")

            # The example projects contain a bunch of imports that can't be
            # resolved, so those are marked with special `# type: ignore`
            # comments that need to be removed
            if file_path.suffix == ".py":
                raw_code = raw_code.replace(
                    "  # type: ignore (hidden from user)", ""
                )
        else:
            raw_code = None

        return Snippet(
            group=group,
            name=name,
            file_path=file_path,
            raw_code=raw_code,
        )

    def get_section(self, section_name: str) -> str:
        assert self.is_text_snippet, self
        assert self.raw_code is not None, self  # For the type checker

        # Find the target section
        lines = self.raw_code.splitlines()
        section_found = False
        result = []

        for line in lines:
            match = SECTION_PATTERN.match(line)

            # No match
            if match is None:
                result.append(line)
                continue

            # Start of the target section?
            if match.group(1) == section_name:
                result = []
                section_found = True
                continue

            # End of the target section?
            if match.group(1) == f"/{section_name}":
                return "\n".join(result)

            # Some other section, drop it
            pass

        # The section was never found
        if not section_found:
            raise KeyError(f"There is no section named `{section_name}`")

        # The section was found, but never closed
        raise ValueError(f"The section `{section_name}` was never closed")

    def stripped_code(self) -> str:
        """
        Returns the given code with all section tags removed.
        """
        assert self.is_text_snippet, self
        assert self.raw_code is not None, self  # For the type checker

        lines = self.raw_code.splitlines()

        # Remove all section tags
        result = []
        for line in lines:
            if SECTION_PATTERN.match(line) is None:
                result.append(line)

        return "\n".join(result)


@functools.lru_cache(maxsize=None)
def _get_all_snippet_paths() -> dict[str, dict[str, Path]]:
    """
    Returns a dictionary containing all available snippets. The snippets are
    organized by group and name.

    The snippets are read from the `snippets` directory when the function is
    first called. The result is cached after that. Because of this, the result
    mustn't be modified.
    """
    # Find all snippet files
    result = {}

    def scan_dir_recursively(group_name: str, path: Path) -> None:
        assert path.is_dir(), path
        assert result is not None

        # Exclude some directories
        if path.name == "__pycache__":
            return

        for fpath in path.iterdir():
            # Directory
            if fpath.is_dir():
                scan_dir_recursively(group_name, fpath)

            # Snippet file
            else:
                name = fpath.name
                group = result.setdefault(group_name, {})
                group[name] = fpath

    # Scan all snippet directories. The first directory is used as a key, the
    # rest just for organization.
    for group_dir in utils.SNIPPETS_DIR.iterdir():
        assert group_dir.is_dir(), group_dir
        scan_dir_recursively(group_dir.name, group_dir)

    return result


def get_snippet_groups() -> set[str]:
    """
    Returns a set of all snippet available groups.
    """
    all_groups = _get_all_snippet_paths()
    return set(all_groups.keys())


@functools.lru_cache(maxsize=None)
def all_snippets_in_group(group: str) -> t.Iterable[Snippet]:
    """
    Returns all snippets in the given group.

    ## Raises

    `KeyError`: If there is no group with the given name.
    """
    all_groups = _get_all_snippet_paths()
    group_dict = all_groups.get(group, {})

    return tuple(
        Snippet.from_path(group, name, file_path)
        for name, file_path in group_dict.items()
    )


@functools.lru_cache(maxsize=None)
def get_snippet(group: str, name: str) -> Snippet:
    """
    Parses and returns the snippet with the given group and name.

    ## Raises

    `KeyError`: If there is no snippet with the given group and name.
    """
    all_groups = _get_all_snippet_paths()

    group_dict = all_groups[group]
    file_path = group_dict[name]

    return Snippet.from_path(group, name, file_path)


@dataclass
class ProjectTemplate:
    """
    Project templates are stored as snippets. This class represents all
    resources necessary for a single project template.
    """

    # Human-readable name of the project template
    name: AvailableTemplatesLiteral

    # How difficult the project is
    level: t.Literal["beginner", "intermediate", "advanced"]

    # A short description of the project template
    summary: str

    # Description of the project template (Markdown)
    description_markdown_source: str

    # The project thumbnail. This is a SVG file.
    thumbnail: Snippet

    # Any pypi packages this project depends on, in the same format as used by
    # `pip`.
    #
    # Example: `{"numpy": ">=1.21.0", "pandas": "^1.3.0"}`
    dependencies: dict[str, str]

    # All snippets which should be included
    asset_snippets: list[Snippet]
    component_snippets: list[Snippet]
    page_snippets: list[Snippet]
    other_python_files: list[Snippet]

    root_init_snippet: Snippet

    # Additional configuration for the app instance
    root_component: str | None
    on_app_start: str | None
    on_session_start: str | None
    default_attachments: list[str] | None

    @property
    def slug(self) -> str:
        return self.name.lower().replace(" ", "-")

    @staticmethod
    def _from_snippet_group(
        snippet_name: str,
        snippets: t.Iterable[Snippet],
    ) -> ProjectTemplate:
        assert (
            snippet_name in t.get_args(AvailableTemplatesLiteral)
            or snippet_name == "Empty"
        ), snippet_name
        name = t.cast(AvailableTemplatesLiteral, snippet_name)

        # Find all snippets needed for the project template
        readme_snippet: Snippet | None = None
        thumbnail_snippet: Snippet | None = None
        metadata: _TemplateConfig | None = None
        root_init_snippet: Snippet | None = None

        asset_snippets: list[Snippet] = []
        python_files: list[Snippet] = []

        for snippet in snippets:
            # README snippet can be recognized by its name
            if snippet.name == "README.md":
                assert readme_snippet is None
                assert snippet.is_text_snippet, snippet.file_path
                readme_snippet = snippet
                continue

            # As is the thumbnail
            if snippet.name == "thumbnail.svg":
                assert thumbnail_snippet is None
                thumbnail_snippet = snippet
                continue

            # And the metadata
            if snippet.name == "meta.json":
                meta_dict: dict[str, t.Any] = copy.deepcopy(DEFAULT_META_DICT)
                meta_dict.update(json.loads(snippet.stripped_code()))
                metadata = _TemplateConfig.from_json(meta_dict)
                continue

            # Others are categorized by the directory they're in
            dir_name = snippet.file_path.parent.name

            if dir_name == "assets":
                asset_snippets.append(snippet)

            elif snippet.file_path.name == "root_init.py":
                assert root_init_snippet is None
                assert snippet.is_text_snippet, snippet.file_path
                root_init_snippet = snippet

            elif snippet.file_path.suffix == ".py":
                python_files.append(snippet)

            else:
                assert False, f"Unrecognized snippet file `{snippet.file_path}`"

        # Make sure everything was found
        assert (
            readme_snippet is not None
        ), f"`README.md` snippet not found for `{name}`"
        assert (
            thumbnail_snippet is not None
        ), f"`thumbnail.svg` snippet not found for {name}"
        assert (
            metadata is not None
        ), f"`meta.json` snippet not found for `{name}`"
        assert (
            root_init_snippet is not None
        ), f"`root_init.py` snippet not found for `{name}`"

        # Further split the Python files into components, pages, and other
        # files. This cannot be done above, because it requires knowledge of
        # where the snippet groups's root directory is placed. This directory in
        # turn is only known once the snippets have been found.
        template_root_dir = root_init_snippet.file_path.parent

        ii = 0
        component_snippets: list[Snippet] = []
        page_snippets: list[Snippet] = []

        while ii < len(python_files):
            snippet = python_files[ii]
            rel_path = snippet.file_path.relative_to(template_root_dir)

            # Component?
            if rel_path.parts[0] == "components":
                del python_files[ii]

                if snippet.name == "__init__.py":
                    continue

                assert snippet.is_text_snippet, snippet.file_path
                component_snippets.append(snippet)

            # Page?
            elif rel_path.parts[0] == "pages":
                del python_files[ii]

                assert snippet.is_text_snippet, snippet.file_path
                page_snippets.append(snippet)

            # Plain old Python file
            else:
                ii += 1

        assert len(page_snippets) > 0, f"No page snippets found for `{name}`"

        # Create the project template
        return ProjectTemplate(
            name=name,
            level=metadata.level,
            summary=metadata.summary,
            description_markdown_source=readme_snippet.stripped_code(),
            thumbnail=thumbnail_snippet,
            dependencies=metadata.dependencies,
            asset_snippets=asset_snippets,
            component_snippets=component_snippets,
            page_snippets=page_snippets,
            other_python_files=python_files,
            root_init_snippet=root_init_snippet,
            root_component=metadata.root_component,
            on_app_start=metadata.on_app_start,
            on_session_start=metadata.on_session_start,
            default_attachments=metadata.default_attachments,
        )


@functools.lru_cache(maxsize=None)
def get_project_templates(include_empty: bool) -> t.Iterable[ProjectTemplate]:
    """
    Iterates over all available project templates.

    `include_empty` controls whether to include the empty template.
    """
    result = []

    # Templates are just snippet groups starting with `project-template-`
    for group_name, snippets in _get_all_snippet_paths().items():
        # Is this a project template?
        template_name = group_name.removeprefix("project-template-")

        if group_name == template_name:
            continue

        # Skip the empty template if it's not requested
        if template_name == "Empty" and not include_empty:
            continue

        # Parse the template
        result.append(
            ProjectTemplate._from_snippet_group(
                template_name,
                [
                    Snippet.from_path(
                        group_name,
                        name,
                        file_path,
                    )
                    for name, file_path in snippets.items()
                ],
            )
        )

    # This function can't simply yield, because of the `lru_cache`. Instead,
    # return something immutable.
    return tuple(result)


@dataclass
class HowtoGuide:
    """
    Represents a how-to guide.
    """

    # A URL-safe unique identifier for the how-to guide
    slug: str

    # A human-readable name of the how-to guide
    title: str

    # The markdown source of the how-to guide. This does not contain a title
    markdown_source: str

    @staticmethod
    def from_snippet(snip: Snippet) -> HowtoGuide:
        """
        Creates a `Howto` instance from a snippet. The snippet must contain
        the howto's markdown source and start with a # heading.
        """
        # Split the markdown source into title and content
        full_source = snip.stripped_code()
        lines = full_source.split("\n", 1)
        assert (
            len(lines) == 2
        ), f"Snippet `{snip.name}` is either missing a title or the content"
        title, content = lines

        # Clean up the title
        title = title.strip()
        assert title.startswith(
            "#"
        ), f"The source for snippet `{snip.name}` does not start with a heading?"
        title = title[1:].strip()

        # Clean up the content
        content = content.strip()

        # Derive the slug from the snippet's name
        assert snip.name.endswith(".md"), snip.name
        slug = snip.name[:-3]
        assert slug == urllib.parse.quote(slug), slug

        # Build the result
        return HowtoGuide(
            slug=slug,
            title=title,
            markdown_source=content,
        )


@functools.lru_cache(maxsize=None)
def get_howto_guides() -> t.Iterable[HowtoGuide]:
    """
    Iterates over all available how-to guides.
    """
    result = []

    for snip in all_snippets_in_group("howtos"):
        result.append(HowtoGuide.from_snippet(snip))

    # This function can't simply yield, because of the `lru_cache`. Instead,
    # return something immutable.
    return tuple(result)
