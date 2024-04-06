from __future__ import annotations

from dataclasses import KW_ONLY, field
from typing import *  # type: ignore

import rio

from .. import components as comps


class GeneratingResponsePlaceholder(rio.Component):
    def build(self) -> rio.Component:
        return rio.Row(
            rio.ProgressCircle(size=1.5),
            rio.Text("Thinking..."),
            spacing=1,
        )
