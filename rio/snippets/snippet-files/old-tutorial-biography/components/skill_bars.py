from typing import *  # type: ignore

import rio


class SkillBars(rio.Component):
    skills: dict[str, int]

    def build(self) -> rio.Component:
        rows = []

        for name, level in self.skills.items():
            rows.append(
                rio.Column(
                    rio.Text(
                        name,
                        align_x=0,
                    ),
                    rio.ProgressBar(
                        level / 10,
                    ),
                )
            )

        return rio.Card(
            rio.Column(
                *rows,
                spacing=0.5,
            ),
        )
