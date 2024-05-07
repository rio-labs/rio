from __future__ import annotations

from typing import Literal

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "CodeExplorer",
]


class CodeExplorer(FundamentalComponent):
    """
    ## Metadata

    public: False
    """

    source_code: str
    build_result: rio.Component
    line_indices_to_component_keys: list[str | None]

    style: Literal["horizontal", "vertical"] = "horizontal"


CodeExplorer._unique_id = "CodeExplorer-builtin"
