from __future__ import annotations

import typing as t

import rio


# <code>
# <header>
@rio.page(
    name="Tic Tac Toe",
    url_segment="",
)
class TicTacToePage(rio.Component):
    # </header>
    # <attributes>
    fields: list[t.Literal["X", "O", ""]] = [""] * 9
    # </attributes>

    # <build>
    def build(self) -> rio.Component:
        # Spawn components for the fields
        field_components: list[rio.Component] = []

        for index, field in enumerate(self.fields):
            field_components.append(rio.Text(f"Field {index}"))

        # Arrange all components in a grid
        return rio.Grid(
            field_components[0:3],
            field_components[3:6],
            field_components[6:9],
            row_spacing=1,
            column_spacing=1,
            align_x=0.5,
        )

    # </build>


# </code>
