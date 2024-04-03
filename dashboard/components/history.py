from __future__ import annotations

import time
from dataclasses import KW_ONLY, field
from typing import *  # type: ignore

import plotly.graph_objects as go
import psutil

import rio

from .. import components as comps


class History(rio.Component):
    timestamps: List[float] = field(default_factory=list)
    values: List[float] = field(default_factory=list)

    @rio.event.periodic(0.5)
    async def on_populate(self) -> None:
        # Add the current time and CPU usage to the lists
        now = time.time()
        self.timestamps.append(now)
        self.values.append(psutil.cpu_percent())

        # Remove any old ones
        while self.timestamps[0] < now - 60:
            del self.timestamps[0]
            del self.values[0]

        await self.force_refresh()

    def build(self) -> rio.Component:
        figure = go.Figure(
            go.Scatter(
                x=self.timestamps,
                y=self.values,
                line={
                    "color": self.session.theme.secondary_color.as_plotly,
                    "width": 4,
                },
                fill="tozeroy",
                fillcolor=self.session.theme.secondary_color.replace(
                    opacity=0.2
                ).as_plotly,
            ),
        )

        figure.update_layout(
            yaxis_range=[0, 100],
            xaxis_showticklabels=False,
            # margin={"t": 0, "r": 0, "b": 0, "l": 0},
        )

        return rio.Plot(
            figure,
            corner_radius=self.session.theme.corner_radius_medium,
        )
