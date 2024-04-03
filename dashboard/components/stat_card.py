from __future__ import annotations

from typing import *  # type: ignore

import rio

from .. import components as comps


class StatCard(rio.Component):
    icon: str
    color: rio.Color

    title: str
    current: str
    maximum: str | None = None

    on_press: rio.EventHandler[[]] = None

    @rio.event.periodic(1)
    async def on_populate(self) -> None:
        await self.force_refresh()

    def _on_press(self) -> None:
        pass

    def build(self) -> rio.Component:
        return rio.Card(
            rio.Column(
                rio.Row(
                    rio.Icon(
                        self.icon,
                        width=3,
                        height=3,
                        align_y=0,
                    ),
                    rio.Column(
                        rio.Text(
                            self.title,
                            style="heading3",
                            align_x=1,
                            margin_bottom=1,
                        ),
                        rio.Spacer(),
                        rio.Text(
                            self.current,
                            align_x=1,
                        ),
                        (
                            rio.Spacer(height=0)
                            if self.maximum is None
                            else rio.Text(
                                f"of {self.maximum}",
                                style="dim",
                                align_x=1,
                            )
                        ),
                        width="grow",
                    ),
                    height="grow",
                ),
                margin=1.5,
            ),
            color=self.color,
            on_press=self._on_press,
        )
