from __future__ import annotations

import functools
import typing as t

from .. import utils
from .project_template import AvailableTemplatesLiteral, ProjectTemplate
from .snippet_manager import Snippet, SnippetManager

__all__ = [
    "AvailableTemplatesLiteral",
    "ProjectTemplate",
    "Snippet",
    "SnippetManager",
    "MANAGER",
    "get_project_templates",
]


# Expose a global instance of the snippet manager
MANAGER = SnippetManager(
    snippet_directory=utils.SNIPPETS_DIR,
)


# Provide functionality to discover all available project templates
@functools.lru_cache(maxsize=None)
def get_project_templates(include_empty: bool) -> t.Iterable[ProjectTemplate]:
    """
    Iterates over all available project templates.

    `include_empty` controls whether to include the empty template.
    """
    result = []

    # Templates are just snippet groups starting with `project-template-`
    for group_name in MANAGER.get_all_snippet_groups():
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
                MANAGER.get_all_snippets_in_group(group_name),
            )
        )

    # This function can't simply yield, because of the `lru_cache`. Instead,
    # return something immutable.
    return tuple(result)
