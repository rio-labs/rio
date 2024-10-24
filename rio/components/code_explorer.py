from __future__ import annotations

import typing as t

from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "CodeExplorer",
]


class CodeExplorer(FundamentalComponent):
    """
    ## Metadata

    `public`: False
    """

    source_code: str
    build_result: rio.Component
    line_indices_to_component_keys: t.Sequence[str | int | None]

    style: t.Literal["horizontal", "vertical"] = "horizontal"

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "line_indices_to_component_keys": self.line_indices_to_component_keys,  # type: ignore
        }


CodeExplorer._unique_id_ = "CodeExplorer-builtin"
