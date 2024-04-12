from __future__ import annotations

from typing import *  # type: ignore

import rio


# <code>
class Field(rio.Component):
    value: Literal["X", "O", ""]
    dim: bool

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

        # For fields that already contain an X or O, show the respective
        # icon.
        #
        # Vary the color based on the player
        color = rio.Color.RED if self.value == "X" else rio.Color.BLUE

        # If a player has won, and this field isn't part of the winning
        # combination, dim it.
        if self.dim:
            color = color.replace(opacity=0.2)

        return rio.Icon(
            "material/close" if self.value == "X" else "material/circle",
            fill=color,
            width=3,
            height=3,
        )


# </code>
