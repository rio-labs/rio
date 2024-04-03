from __future__ import annotations

from typing import *  # type: ignore

import rio

from .. import components as comps


class Sidebar(rio.Component):
    def build(self) -> rio.Component:
        return rio.Card(
            rio.SwitcherBar(
                icons=[
                    "castle",
                    "archive",
                    "settings",
                ],
                names=[
                    "Dash",
                    "Project",
                    "Settings",
                ],
                values=[
                    "dashboard",
                    "projects",
                    "settings",
                ],
                orientation="vertical",
                align_y=0,
                margin=0.4,
            ),
            corner_radius=0,
        )
