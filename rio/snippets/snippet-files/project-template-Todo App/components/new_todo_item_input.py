from __future__ import annotations

# <additional-imports>
import datetime
from dataclasses import field

import rio

from .. import data_models

# </additional-imports>


# <component>
class NewTodoItemInput(rio.Component):
    """
    A component that lets the user create a new `TodoItem`.

    Includes a `TextInput` for the title and a button. Pressing the button or
    the "Enter" key will create a new `TodoItem`.
    """

    on_input: rio.EventHandler[data_models.TodoItem]

    # This is a private field that we need for an attribute binding. We don't
    # want to create a constructor parameter for this field, so we set
    # `init=False`.
    _title: str = field(init=False, default="")

    async def _on_confirm(
        self, _: rio.TextInputConfirmEvent | None = None
    ) -> None:
        # No title entered? Then we won't do anything
        if not self._title:
            return

        # Create the new `TodoItem` and call our `on_input` event handler
        new_todo_item = data_models.TodoItem(
            title=self._title,
            creation_time=datetime.datetime.now().astimezone(),
        )
        await self.call_event_handler(self.on_input, new_todo_item)

        # Reset the `TextInput`
        self._title = ""

    def build(self) -> rio.Component:
        return rio.Row(
            rio.TextInput(
                label="Enter a new todo item",
                text=self.bind()._title,
                on_confirm=self._on_confirm,
                grow_x=True,
            ),
            rio.IconButton(
                "material/add",
                min_size=2.5,
                on_press=self._on_confirm,
                margin_right=0.5,
            ),
            spacing=1,
        )


# </component>
