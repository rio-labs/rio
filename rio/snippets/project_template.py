from __future__ import annotations

import copy
import dataclasses
import json
import typing as t

import typing_extensions as te

import rio

from .. import serialization
from .snippet_manager import Snippet

__all__ = [
    "ProjectTemplate",
]


# Contains default values for the `meta.json` file
DEFAULT_META_DICT = {
    "dependencies": {},
    "rootComponent": None,
    "onAppStart": None,
    "onSessionStart": None,
    "defaultAttachments": None,
    "theme": None,
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
    "Dashboard Better Name",  # TODO: better name :)
    "Multipage Website",
    "Sales Dashboard",
    "Simple CRUD",
    "Tic-Tac-Toe",
    "Todo App",
]


@dataclasses.dataclass
class _TemplateConfig:
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

    # Whether projects based on this template are ready to run out of the box,
    # without any modifications needed. For example, a template that requires an
    # API key to be set up is not ready to run.
    ready_to_run: bool

    # Whether projects based on this template supports mobile
    supports_mobile: bool

    # Additional parameters to pass to the app instance
    root_component: str | None
    on_app_start: str | None
    on_session_start: str | None
    default_attachments: list[str] | None
    theme: str | None


@dataclasses.dataclass
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

    # Whether projects based on this template are ready to run out of the box,
    # without any modifications needed. For example, a template that requires an
    # API key to be set up is not ready to run.
    ready_to_run: bool

    # Whether projects based on this template supports mobile
    supports_mobile: bool

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
    theme: str | None = None

    @property
    def slug(self) -> str:
        return self.name.lower().replace(" ", "-")

    @property
    def live_example_url(self) -> rio.URL | None:
        """
        If there is a publicly hosted demo for this template, return the URL to
        it. Otherwise, return `None`.
        """
        # All examples are hosted, provided they don't require any changes by
        # the user.
        if self.ready_to_run:
            return rio.URL(f"https://rio.dev/live-example/{self.slug}")

        return None

    @property
    def source_code_url(self) -> rio.URL:
        """
        All built-in templates have their source code publicly available on GitHub. This
        returns the URL to the repository.
        """
        return rio.URL(
            f"https://github.com/rio-labs/rio-templates/tree/main/{self.slug}"
        )

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
            # TODO: delete thumbnail.svg after all templates have thumbnail.png
            if snippet.name in ["thumbnail.svg", "thumbnail.png"]:
                assert thumbnail_snippet is None
                thumbnail_snippet = snippet
                continue

            # And the metadata
            if snippet.name == "meta.json":
                meta_dict: dict[str, t.Any] = copy.deepcopy(DEFAULT_META_DICT)
                meta_dict.update(json.loads(snippet.stripped_code()))
                metadata = serialization.json_serde.from_json(
                    _TemplateConfig,
                    meta_dict,
                )
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

            elif snippet.file_path.suffix in [
                ".jpg",
                ".png",
                ".jpeg",
                ".svg",
                ".webp",
            ]:
                asset_snippets.append(snippet)

            else:
                assert False, f"Unrecognized snippet file `{snippet.file_path}`"

        # Make sure everything was found
        assert readme_snippet is not None, (
            f"`README.md` snippet not found for `{name}`"
        )
        assert thumbnail_snippet is not None, (
            f"`thumbnail.svg` snippet not found for {name}"
        )
        assert metadata is not None, (
            f"`meta.json` snippet not found for `{name}`"
        )
        assert root_init_snippet is not None, (
            f"`root_init.py` snippet not found for `{name}`"
        )

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
            theme=metadata.theme,
            ready_to_run=metadata.ready_to_run,
            supports_mobile=metadata.supports_mobile,
        )
