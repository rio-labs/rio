from __future__ import annotations

from typing import *  # type: ignore

import rio


# <additional-imports>
from ..data_models import TodoItem
# </additional-imports>


# <component>
ICON_BUTTON_SIZE = 2.5


class TodoItemComponent(rio.Component):
    """
    Displays a single `TodoItem`.

    Includes the `TodoItem`'s title and creation date, a button that marks it as
    completed, and a button that deletes it.
    """

    todo_item: TodoItem
    on_completed: rio.EventHandler[[]] = None
    on_deleted: rio.EventHandler[[]] = None

    async def _mark_as_completed(self) -> None:
        # If it's already completed, there's nothing to do
        if self.todo_item.completed:
            return

        self.todo_item.completed = True
        await self.call_event_handler(self.on_completed)

        # Rio doesn't know that we modified the TodoItem, so it won't
        # automatically rebuild this component. We have to manually trigger a
        # rebuild.
        await self.force_refresh()

    def build(self) -> rio.Component:
        return rio.Card(
            rio.Row(
                # The "mark as complete" button
                rio.IconButton(
                    "material/check",
                    size=ICON_BUTTON_SIZE,
                    color="success" if self.todo_item.completed else "neutral",
                    on_press=self._mark_as_completed,
                ),
                # The title and creation date
                rio.Column(
                    rio.Text(self.todo_item.title, justify="left"),
                    rio.Text(
                        f"{self.todo_item.creation_time:%A, %x}",
                        justify="left",
                        style="dim",
                    ),
                ),
                rio.Spacer(),
                # The "delete" button
                rio.IconButton(
                    "material/delete",
                    size=ICON_BUTTON_SIZE,
                    on_press=self.on_deleted,
                ),
                spacing=0.5,
            ),
            color="background",
            elevate_on_hover=True,
            corner_radius=999,
        )


# </component>
