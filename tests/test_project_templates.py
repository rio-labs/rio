"""
Project templates are stored using Rio's snippet system.

This file ensures that the snippets for project templates match expectations.
"""

from __future__ import annotations

import tempfile
import typing as t
from pathlib import Path

import pytest

import rio.cli
import rio.snippets


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
    Ensures that the snippets for project templates match expectations, by
    parsing them.
    """
    # Iterate over all templates. This forces them to be parsed
    for _ in rio.snippets.get_project_templates(include_empty=True):
        pass


def test_available_template_literal_matches_templates() -> None:
    """
    Rio defines a literal type which corresponds to all available project
    templates. This test verifies that the literal and the actual templates
    match.
    """
    # Find all templates according to the literal
    templates_according_to_literal = set(
        t.get_args(rio.snippets.AvailableTemplatesLiteral)
    ) | {"Empty"}

    # Find all defined templates
    templates_according_to_snippets = {
        template.name
        for template in rio.snippets.get_project_templates(include_empty=True)
    }

    # They must match
    assert templates_according_to_literal == templates_according_to_snippets


@pytest.mark.parametrize(
    "template",
    rio.snippets.get_project_templates(include_empty=True),
)
def test_instantiate_template(template: rio.snippets.ProjectTemplate) -> None:
    """
    Instantiates all templates to ensure that they can be instantiated without
    crashing.
    """

    # Create a temporary directory for the project
    with tempfile.TemporaryDirectory() as project_directory_str:
        # Instantiate the template
        rio.cli.project_setup.create_project(
            raw_name=f"Test Project {template.name}",
            type="website",
            template_name=template.name,
            target_parent_directory=Path(project_directory_str),
        )

        # There are no further checks here. The test simply makes sure there is
        # no crash during the instantiation.
