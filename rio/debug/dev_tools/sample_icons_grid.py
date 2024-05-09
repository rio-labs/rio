import functools
import random
from typing import *  # type: ignore

import rio
import rio.icon_registry

ICON_SET = "material"
GRID_N_ROWS = 12
GRID_N_COLUMNS = 6


# Choose icons to display
def find_icons_to_display() -> Iterable[str]:
    # Get a list of all available icons
    names_and_variants: list[tuple[str, str | None]] = list(
        rio.icon_registry.IconRegistry.get_singleton().all_icons_in_set(
            ICON_SET
        )
    )

    # Choose some at random
    result = random.sample(names_and_variants, GRID_N_ROWS * GRID_N_COLUMNS)

    # Convert to strings
    for name, variant in result:
        yield (
            f"{ICON_SET}/{name}"
            if variant is None
            else f"{ICON_SET}/{name}:{variant}"
        )


DISPLAYED_ICON_NAMES: list[str] = list(find_icons_to_display())


class SampleIconsGrid(rio.Component):
    """
    Displays a raster of icons.
    """

    on_select_icon: rio.EventHandler[str] = None

    async def _on_select_icon(self, icon_name: str) -> None:
        """
        Called when an icon is selected.
        """
        await self.call_event_handler(self.on_select_icon, icon_name)

    async def _on_randomize(self) -> None:
        global DISPLAYED_ICON_NAMES
        DISPLAYED_ICON_NAMES = list(find_icons_to_display())

        await self.force_refresh()

    def build(self) -> rio.Component:
        # Build a flat list of all icons
        icons_flat: list[rio.Component] = [
            rio.IconButton(
                icon=icon,
                size=3,
                style="plain",
                on_press=functools.partial(self._on_select_icon, icon),
                key=icon,
            )
            for icon in DISPLAYED_ICON_NAMES
        ]

        # Split the flat list into rows
        icon_rows: list[list[rio.Component]] = [
            icons_flat[i : i + GRID_N_COLUMNS]
            for i in range(0, len(icons_flat), GRID_N_COLUMNS)
        ]

        # Build the resulting grid
        return rio.Grid(
            *icon_rows,
            rio.Button(
                "Randomize",
                icon="material/refresh",
                style="plain",
                on_press=self._on_randomize,
                align_y=0.5,
            ),
            row_spacing=0.5,
            column_spacing=0.5,
        )
