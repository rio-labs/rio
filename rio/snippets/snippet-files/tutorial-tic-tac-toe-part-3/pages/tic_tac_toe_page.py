from __future__ import annotations

from typing import *  # type: ignore

import rio

from .. import components as comps


# <code>
class TicTacToePage(rio.Component):
    # The contents of all fields. Each field can contain an X, an O, or be
    # empty. The initial state is an empty board.
    fields: list[Literal["X", "O", ""]] = [""] * 9

    def build(self) -> rio.Component:
        # Spawn components for the fields
        field_components: list[rio.Component] = []

        for index, field in enumerate(self.fields):
            comps.Field(
                value=field,
            )

        # Arrange all components in a grid
        return rio.Grid(
            field_components[0:3],
            field_components[3:6],
            field_components[6:9],
            row_spacing=1,
            column_spacing=1,
            align_x=0.5,
        )


# </code>
