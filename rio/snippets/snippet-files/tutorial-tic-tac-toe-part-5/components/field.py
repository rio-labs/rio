from __future__ import annotations

import typing as t

import rio


# <code>
class Field(rio.Component):
    value: t.Literal["X", "O", ""]
    dim: bool

    on_press: rio.EventHandler[[]] = None

    def build(self) -> rio.Component:
        # If the field is empty, allow the player to press on it. Since buttons
        # would look out of place here, cards are a nice alternative.
        if self.value == "":
            return rio.Card(
                content=rio.Spacer(
                    min_width=3,
                    min_height=3,
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

        # If a player has won, and this field isn't part of the winning
        # combination, dim it.
        if self.dim:
            color = color.replace(opacity=0.2)

        return rio.Icon(
            icon=icon,
            fill=color,
            min_width=3,
            min_height=3,
        )


# </code>
