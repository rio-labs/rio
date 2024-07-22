from __future__ import annotations

from typing import Literal, Sequence

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
    line_indices_to_component_keys: Sequence[str | int | None]

    style: Literal["horizontal", "vertical"] = "horizontal"

    def _custom_serialize(self) -> JsonDoc:
        return {
            "line_indices_to_component_keys": self.line_indices_to_component_keys,  # type: ignore
        }


CodeExplorer._unique_id = "CodeExplorer-builtin"
