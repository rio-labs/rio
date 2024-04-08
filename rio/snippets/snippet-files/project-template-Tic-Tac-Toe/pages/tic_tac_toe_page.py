from __future__ import annotations

# <additional-imports>
import functools
from dataclasses import field
from typing import *  # type: ignore

import rio

# </additional-imports>


# <component>
class TicTacToePage(rio.Component):
    """
    This page contains the Tic Tac Toe game. It consists of 9 fields, which
    display either an X or an O. Players can press on empty fields to set their
    respective mark. You know the game.

    Since this game is so simple, there is no further components in the project.
    Everything is contained right in this class.
    """

    # The contents of all fields
    fields: list[Literal["X", "O", ""]] = field(default_factory=lambda: [""] * 9)

    # The player who is currently on turn
    player: Literal["X", "O"] = "X"

    # The winner of the game, if any
    winner: Literal["X", "O", "draw"] | None = None

    # If there is a winner, these are the indices of the fields which made them
    # win
    winning_indices: set[int] = field(default_factory=set)

    def find_winner(self) -> None:
        """
        Look if there is a winner on the board, and stores it in the component's
        state. Also updates the winning indices accordingly.
        """
        # Create a list of all possible winning combinations. If all of these
        # indices have the same value, then that value is the winner.
        winning_combinations = [
            [0, 1, 2],  # Top row
            [3, 4, 5],  # Middle row
            [6, 7, 8],  # Bottom row
            [0, 3, 6],  # Left column
            [1, 4, 7],  # Middle column
            [2, 5, 8],  # Right column
            [0, 4, 8],  # Top-left to bottom-right diagonal
            [2, 4, 6],  # Top-right to bottom-left diagonal
        ]

        # Look for winners
        for combination in winning_combinations:
            values = [self.fields[i] for i in combination]
            if values.count("X") == 3:
                self.winner = "X"
                self.winning_indices = set(combination)
                return

            if values.count("O") == 3:
                self.winner = "O"
                self.winning_indices = set(combination)
                return

        # If no fields are empty, it's a draw
        if "" not in self.fields:
            self.winner = "draw"
            return

        # There is no winner yet
        pass

    async def on_press(self, index: int) -> None:
        """
        This function reacts to presses on the fields, and updates the game
        state accordingly.
        """

        # If the game is already over, don't do anything
        if self.winner:
            return

        # Set the field on that index
        self.fields[index] = self.player

        # Next player
        self.player = "X" if self.player == "O" else "O"

        # See if there is a winner
        self.find_winner()

    def on_reset(self) -> None:
        """
        Reset the game to its initial state.
        """
        self.fields = [""] * 9
        self.player = "X"
        self.winner = None
        self.winning_indices = set()

    def build(self) -> rio.Component:
        # Spawn components for the fields
        field_components: list[rio.Component] = []
        field_size = 3

        for index, field in enumerate(self.fields):
            # Allow the player to press on empty fields. Since buttons would
            # look out of place here, cards are a nice alternative.
            if field == "":
                field_components.append(
                    rio.Card(
                        content=rio.Spacer(
                            width=field_size,
                            height=field_size,
                        ),
                        on_press=functools.partial(self.on_press, index),
                    )
                )

            # For fields that already contain an X or O, show the respective
            # icon
            else:
                # Vary the color based on the player
                color = rio.Color.RED if field == "X" else rio.Color.BLUE

                # If a player has won highlight the winning fields
                if self.winner in ("X", "O") and index not in self.winning_indices:
                    color = color.replace(opacity=0.3)

                # Create the icon to represent the field
                field_components.append(
                    rio.Icon(
                        "material/close" if field == "X" else "material/circle",
                        fill=color,
                        width=field_size,
                        height=field_size,
                    )
                )

        # Come up with a status message
        if self.winner in ("X", "O"):
            message = f"{self.winner} has won!"
        elif self.winner == "draw":
            message = "It's a draw!"
        else:
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
                style="plain",
                on_press=self.on_reset,
            ),
            spacing=2,
            margin=2,
            align_x=0.5,
            align_y=0.0,
        )


# </component>
