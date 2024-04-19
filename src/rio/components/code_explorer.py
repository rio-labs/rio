from __future__ import annotations

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "CodeExplorer",
]


class CodeExplorer(FundamentalComponent):
    # TODO
    source_code: str
    build_result: rio.Component

    line_indices_to_component_keys: list[str | None]


CodeExplorer._unique_id = "CodeExplorer-builtin"
