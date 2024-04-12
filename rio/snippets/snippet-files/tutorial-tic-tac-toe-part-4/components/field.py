from __future__ import annotations

from typing import *  # type: ignore

import rio


# <code>
class Field(rio.Component):
    value: Literal["X", "O", ""]

    on_press: rio.EventHandler[[]] = None

    def build(self) -> rio.Component:
        # If the field is empty, allow the player to press on it. Since buttons
        # would look out of place here, cards are a nice alternative.
        if self.value == "":
            return rio.Card(
                content=rio.Spacer(
                    width=3,
                    height=3,
                ),
                on_press=self.on_press,
            )

        # For fields that already contain an X or O, show the respective icon.
        # Also vary the color based on the player.
        if self.value == "X":
            color = rio.Color.RED
            icon = "material/close"
        else:
            color = rio.Color.BLUE
            icon = "material/circle"

        return rio.Icon(
            icon=icon,
            fill=color,
            width=3,
            height=3,
        )


# </code>
