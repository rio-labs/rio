from __future__ import annotations

import functools
from typing import *  # type: ignore

import rio

from .. import components as comps

# <additional-imports>
import functools

from ..data_models import TodoItem, TodoAppSettings
# </additional-imports>


# <component>
class TodoListPage(rio.Component):
    """
    This page displays the entire GUI for the Todo App.

    There's a status message at the top, then a list of `TodoItem`s, and finally
    an input form that lets the user create a new `TodoItem`.
    """

    async def _add_new_todo_item(self, todo_item: TodoItem) -> None:
        # Append the new item to the list
        settings = self.session[TodoAppSettings]
        settings.todo_items.append(todo_item)

        # Save the settings and rebuild this component
        await self._on_settings_changed()

    async def _delete_todo_item(self, todo_item: TodoItem) -> None:
        # Remove the item from the list
        settings = self.session[TodoAppSettings]
        settings.todo_items.remove(todo_item)

        # Save the settings and rebuild this component
        await self._on_settings_changed()

    async def _on_settings_changed(self) -> None:
        # Re-attach the settings to save them
        self.session.attach(self.session[TodoAppSettings])

        # Rio doesn't know that this component needs to be rebuilt, since it
        # doesn't have any properties that have changed. We'll tell rio to
        # rebuild it by calling `self.force_refresh()`.
        await self.force_refresh()

    def build(self) -> rio.Component:
        settings = self.session[TodoAppSettings]

        # Display a status message depending on the number of unfinished items
        num_incomplete_items = sum(
            not todo_item.completed for todo_item in settings.todo_items
        )
        if num_incomplete_items > 0:
            status_text = f'You have {num_incomplete_items} unfinished task{"" if num_incomplete_items == 1 else "s"} 📋'
        elif settings.todo_items:
            status_text = "You have completed all your tasks 🎉"
        else:
            status_text = "You don't have anything to do 💤"

        return rio.Column(
            # Status message
            rio.Text(status_text),
            # List of todo items
            rio.Column(
                *[
                    comps.TodoItemComponent(
                        todo_item,
                        on_completed=self._on_settings_changed,
                        on_deleted=functools.partial(
                            self._delete_todo_item, todo_item
                        ),
                    )
                    for todo_item in settings.todo_items
                ],
                rio.Spacer(),
                height="grow",
            ),
            # Input for new todo items
            comps.NewTodoItemInput(
                on_input=self._add_new_todo_item,
            ),
            margin=1,
            margin_bottom=0,
            spacing=1,
        )


# </component>
