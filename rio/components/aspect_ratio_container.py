from __future__ import annotations

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "AspectRatioContainer",
]


class AspectRatioContainer(FundamentalComponent):
    # TODO

    content: rio.Component
    aspect_ratio: float


AspectRatioContainer._unique_id = "AspectRatioContainer-builtin"
