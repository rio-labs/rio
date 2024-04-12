from pathlib import Path
from typing import *  # type: ignore

import rio


class AboutMe(rio.Component):
    def build(self) -> rio.Component:
        return rio.Row(
            rio.Image(
                Path("me.jpg"),
                width=11,
                height=11,
                corner_radius=99999,
                fill_mode="zoom",
                margin_right=2,
            ),
            rio.Column(
                rio.Text(
                    "Jane Doe",
                    style="heading1",
                    justify='left',
                ),
                rio.Text(
                    "Data Analyst",
                    justify='left',
                ),
                rio.Text(
                    "AI Researcher",
                    justify='left',
                ),
                rio.Text(
                    "Python Developer",
                    justify='left',
                ),
                spacing=0.5,
                align_y=0,
                width="grow",
            ),
            width="grow",
        )
