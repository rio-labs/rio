from __future__ import annotations

import functools
import typing as t

import rio

from .. import components as comps


# <code>
@rio.page(
    name="Tic Tac Toe",
    url_segment="",
)
class TicTacToePage(rio.Component):
    # The contents of all fields. Each field can contain an X, an O, or be
    # empty. The initial state is an empty board.
    fields: list[t.Literal["X", "O", ""]] = [""] * 9

    # <new-attributes>
    # The player who is currently on turn
    player: t.Literal["X", "O"] = "X"
    # </new-attributes>

    # <on-press>
    def on_press(self, index: int) -> None:
        """
        This function reacts to presses on the fields, and updates the game
        state accordingly.
        """

        # Set the field on that index
        self.fields[index] = self.player

        # Next player
        self.player = "X" if self.player == "O" else "O"

    # </on-press>

    # <on-reset>
    def on_reset(self) -> None:
        """
        Reset the game to its initial state.
        """
        self.fields = [""] * 9
        self.player = "X"

    # </on-reset>

    # <build>
    def build(self) -> rio.Component:
        # Spawn components for the fields
        field_components: list[rio.Component] = []

        for index, field in enumerate(self.fields):
            field_components.append(
                comps.Field(
                    value=field,
                    on_press=functools.partial(self.on_press, index),
                )
            )

        # Come up with a status message
        message = f"{self.player}'s turn"

        # Arrange all components in a grid
        return rio.Column(
            rio.Text(message, style="heading1"),
            rio.Grid(
                field_components[0:3],
                field_components[3:6],
                field_components[6:9],
                row_spacing=1,
                column_spacing=1,
                align_x=0.5,
            ),
            rio.Button(
                "Reset",
                icon="material/refresh",
                style="colored-text",
                on_press=self.on_reset,
            ),
            spacing=2,
            margin=2,
            align_x=0.5,
            align_y=0.0,
        )

    # </build>


# </code>
