from __future__ import annotations

from dataclasses import KW_ONLY, field
from typing import *  # type: ignore

import rio

from .. import components as comps


class ChatSuggestionCard(rio.Component):
    icon: str
    text: str

    on_press: rio.EventHandler[str] = None

    async def _on_press(self) -> None:
        await self.call_event_handler(self.on_press, self.text)

    def build(self) -> rio.Component:
        return rio.Card(
            rio.Column(
                rio.Icon(self.icon),
                rio.Text(
                    self.text,
                    multiline=True,
                    height="grow",
                    align_y=0.5,
                ),
                rio.Button(
                    "Ask",
                    icon="navigate-next",
                    style="minor",
                    on_press=self._on_press,
                ),
                spacing=0.6,
                margin=1,
            ),
        )
