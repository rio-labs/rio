"""
Project templates are stored using Rio's snippet system.

This file ensures that the snippets for project templates match expectations.
"""

from __future__ import annotations
import rio.snippets
from typing import *  # type: ignore
import json


def test_empty_template_exists() -> None:
    """
    The "Empty" template is special, because it is used as a fallback if no
    real template is selected. It must exist.
    """

    for template in rio.snippets.get_project_templates(include_empty=True):
        if template.name == "Empty":
            return

    raise AssertionError("The `Empty` template is missing.")


def test_template_structure_is_valid() -> None:
    """
    Ensures that the snippets for project templates match expectations.
    """

    for group_name, snippets in rio.snippets._get_all_snippet_paths().items():
        # Only care about project templates
        if not group_name.startswith("project-template-"):
            continue

        # Parse the template
        found_readme: bool = False
        found_thumbnail: bool = False
        metadata: rio.snippets._TemplateConfig | None = None

        for name, file_path in snippets.items():
            dir_name = file_path.parent.name

            print(name, file_path)

            # Readme
            if name == "README.md":
                found_readme = True

                # The readme mustn't start with a title. This allows imputing one
                # when creating a new project.
                contents = file_path.read_text().strip()
                assert not contents.startswith(
                    "#"
                ), f"`README.md` in `{group_name}` must not start with a title."

                continue

            # Thumbnail
            if name == "thumbnail.svg":
                found_thumbnail = True
                continue

            # Metadata
            if name == "meta.json":
                meta_dict = json.loads(file_path.read_text())
                metadata = rio.snippets._TemplateConfig.from_json(meta_dict)
                continue

            # Assets have few requirements
            if dir_name == "assets":
                continue

            # Python files have additional requirements
            if dir_name in ("components", "pages"):
                # Valid name
                assert file_path.stem.isidentifier(), f"Invalid snippet name: `{name}`"
                assert (
                    file_path.stem == file_path.stem.lower()
                ), f"Invalid snippet name: `{name}`"

                # Don't care for `__init__.py`
                if file_path.name == "__init__.py":
                    continue

                # Make sure there's a `<component>` section
                snippet = rio.snippets.Snippet.from_path(
                    group_name, file_path.name, file_path
                )
                try:
                    snippet.get_section("component")
                except KeyError:
                    assert (
                        False
                    ), f"Snippet `{name}` is missing a `<component>` section."

                continue

            # Invalid file
            assert (
                False
            ), f"The snippet `{name}` is located in an unknown directory named `{dir_name}`."

        assert found_readme
        assert found_thumbnail
        assert metadata is not None


def test_available_template_literal_matches_templates() -> None:
    """
    Rio defines a literal type which corresponds to all available project
    templates. This test verifies that the literal and the actual templates
    match.
    """
    # Find all templates according to the literal
    templates_according_to_literal = set(
        get_args(rio.snippets.AvailableTemplatesLiteral)
    ) | {"Empty"}

    # Find all defined templates
    templates_according_to_snippets = {
        template.name
        for template in rio.snippets.get_project_templates(include_empty=True)
    }

    # They must match
    assert templates_according_to_literal == templates_according_to_snippets
