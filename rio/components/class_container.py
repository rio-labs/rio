from __future__ import annotations

import typing as t

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "ClassContainer",
]


class ClassContainer(FundamentalComponent):
    """
    A Component which holds a single child.

    Component which holds a single child, and applies a list of CSS classes to
    it. This is enough to implement several components, preventing the need to
    create a whole bunch of almost identical JavaScript components.

    This component is only intended for internal use and is not part of the
    public API.


    ## Attributes

    `content`: The child component to apply the classes to.

    `classes`: The list of classes to apply to the child component.


    ## Metadata

    `public`: False
    """

    content: rio.Component | None
    classes: t.Sequence[str]

    def _get_debug_details_(self) -> dict[str, t.Any]:
        result = super()._get_debug_details_()
        result.pop("classes")
        return result


ClassContainer._unique_id_ = "ClassContainer-builtin"
