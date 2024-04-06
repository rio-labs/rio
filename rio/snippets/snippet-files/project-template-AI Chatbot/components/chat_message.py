from __future__ import annotations

from dataclasses import KW_ONLY, field
from typing import *  # type: ignore

import rio

from .. import components as comps
from .. import conversation


class ChatMessage(rio.Component):
    model: conversation.ChatMessage

    def build(self) -> rio.Component:
        if self.model.role == "user":
            icon = "rio/logo"
            color = "neutral"
        else:
            icon = "castle"
            color = "background"

        return rio.Row(
            rio.Card(
                rio.Icon(
                    icon,
                    width=2,
                    height=2,
                    margin=0.8,
                ),
                corner_radius=99999,
                color="neutral",
                margin=0.5,
                align_y=0,
            ),
            rio.Card(
                rio.MarkdownView(
                    self.model.text,
                    # multiline=True,
                    margin=1.5,
                ),
                width="grow",
                color=color,
            ),
        )
