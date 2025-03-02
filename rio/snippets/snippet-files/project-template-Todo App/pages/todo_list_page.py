from __future__ import annotations

# <additional-imports>
import functools

import rio

from .. import components as comps
from .. import data_models

# </additional-imports>


# <component>
@rio.page(
    name="Todo List",
    url_segment="",
)
class TodoListPage(rio.Component):
    """
    This page displays the entire GUI for the Todo App.

    There's a status message at the top, then a list of `TodoItem`s, and finally
    an input form that lets the user create a new `TodoItem`.
    """

    def _add_new_todo_item(self, todo_item: data_models.TodoItem) -> None:
        # Append the new item to the list
        settings = self.session[data_models.TodoAppSettings]
        settings.todo_items.append(todo_item)

        # Save the settings and rebuild this component
        self._on_settings_changed()

    def _delete_todo_item(self, todo_item: data_models.TodoItem) -> None:
        # Remove the item from the list
        settings = self.session[data_models.TodoAppSettings]
        settings.todo_items.remove(todo_item)

        # Save the settings and rebuild this component
        self._on_settings_changed()

    def _on_settings_changed(self) -> None:
        # Re-attach the settings to save them
        self.session.attach(self.session[data_models.TodoAppSettings])

        # Rio doesn't know that this component needs to be rebuilt, since it
        # doesn't have any properties that have changed. We'll tell rio to
        # rebuild it by calling `self.force_refresh()`.
        self.force_refresh()

    def build(self) -> rio.Component:
        settings = self.session[data_models.TodoAppSettings]

        # Display a status message depending on the number of unfinished items
        num_incomplete_items = sum(
            not todo_item.completed for todo_item in settings.todo_items
        )
        if num_incomplete_items > 0:
            status_text = f"You have {num_incomplete_items} unfinished task{'' if num_incomplete_items == 1 else 's'} 📋"
        elif settings.todo_items:
            status_text = "You have completed all your tasks 🎉"
        else:
            status_text = "You don't have anything to do 💤"

        return rio.Column(
            # Status message
            rio.Text(
                status_text,
                justify="center",
            ),
            # Input for new todo items
            comps.NewTodoItemInput(
                on_input=self._add_new_todo_item,
            ),
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
                grow_y=True,
            ),
            margin=1,
            margin_top=2,
            spacing=1,
            # Adjust the layout according to the window width. On larger
            # screens, the application will have a fixed width, while on smaller
            # screens, it will occupy the entire screen.
            min_width=40 if self.session.window_width > 60 else 0,
            align_x=0.5 if self.session.window_width > 60 else None,
        )


# </component>
