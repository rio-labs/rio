from __future__ import annotations

from typing import *  # type: ignore

import rio


# <component>
class Field(rio.Component):
    """
    This component represents a single field in the Tic Tac Toe game. It can
    contain an X, an O, or be empty. If the field is empty, the player can press
    on it to set their respective mark.
    """

    # The current value of the field.
    value: Literal["X", "O", ""]

    # If this is `True`, the field will dim its content. This allows the game to
    # dim any fields that are not part of the winning combination when a player
    # has won.
    dim: bool

    # The game needs to know when a player presses on a field, so it can update
    # the board accordingly. This custom event handler serves that purpose.
    on_press: rio.EventHandler[[]] = None

    def build(self) -> rio.Component:
        # We'll need to specify the size of several components. This variable
        # makes it easier to adjust the size of the fields.
        field_size = 3

        # If the field is empty, allow the player to press on it. Since buttons
        # would look out of place here, cards are a nice alternative.
        if self.value == "":
            return rio.Card(
                content=rio.Spacer(
                    width=field_size,
                    height=field_size,
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

        # Create the icon to represent the field
        return rio.Icon(
            "material/close" if self.value == "X" else "material/circle",
            fill=color,
            width=field_size,
            height=field_size,
        )


# </component>
