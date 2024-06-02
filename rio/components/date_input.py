from __future__ import annotations

import random
from dataclasses import KW_ONLY
from datetime import date

import rio

from .. import components as comps
from .component import Component

__all__ = [
    "DateInput",
]


class DateInput(Component):
    """
    Allows the user to pick a date from a calendar.

    DateInputs are similar in appearance to `TextInput` and `NumberInput`, but
    allow the user to pick a date from a calendar, rather than text or number.
    When pressed, a calendar will pop-up, allowing the user to select a date.

    This makes for a compact component, which still allows the user to visually
    select a date.

    For a larger component which permanently displays a calendar, consider using
    `rio.Calendar`.


    ## Attributes

    `value`: The currently selected date.

    `label`: A short text to display next to the input field.

    `on_change`: Triggered whenever the user selects a new date.


    ## Examples

    Here's a simple example that allows the user to select a data and displays
    it back to them:

    ```python
    from datetime import date

    class MyComponent(rio.Component):
        value: date = date.today()

        def build(self) -> rio.Component:
            return rio.Column(
                rio.DateInput(
                    # In order to retrieve a value from the component, we'll
                    # use an attribute binding. This way our own value will
                    # be updated whenever the user changes the value.
                    value=self.bind().value,
                    label="Pick a Date",
                ),
                rio.Text(f"You've selected: {self.value}"),
            )
    ```

    Alternatively you can also attach an event handler to react to changes. This
    is a little more verbose, but allows you to run arbitrary code when the user
    picks a new date:

    ```python
    from datetime import date

    class MyComponent(rio.Component):
        value: date = date.today()

        def on_value_change(self, event: rio.DateChangeEvent):
            # This function will be called whenever the input's value
            # changes. We'll display the new value in addition to updating
            # our own attribute.
            self.value = event.value
            print(f"You've selected: {self.value}")

        def build(self) -> rio.Component:
            return rio.DateInput(
                value=self.value,
                label="Pick a Date",
                on_change=self.on_value_change,
            )
    ```


    ## Metadata

    `experimental`: True
    """

    value: date

    _: KW_ONLY

    label: str = ""
    on_change: rio.EventHandler[rio.DateChangeEvent] = None

    _is_open: bool = False

    async def _on_value_change(self, event: rio.DateChangeEvent) -> None:
        # Close the date picker
        self._is_open = False

        # Chain the event handler
        await self.call_event_handler(self.on_change, event)

    def _on_toggle_open(self, _: rio.PressEvent) -> None:
        self._is_open = not self._is_open

    def _on_close(self) -> None:
        self._is_open = False

    def build(self) -> rio.Component:
        return rio.Popup(
            # Place a fake textbox. It's only used for styling and displaying
            # the label, if any
            anchor=rio.Stack(
                rio.TextInput(
                    label=self.label,
                    text=self.value.strftime(self.session._date_format_string),
                    is_sensitive=False,
                ),
                # This suppresses any clicks on the text input and opens the
                # calender instead
                rio.MouseEventListener(
                    rio.Rectangle(
                        content=rio.Icon(
                            "material/calendar-today:fill",
                            fill="dim",
                            height=1.5,
                            margin_right=0.5,
                            margin_bottom=0.5,
                            align_x=1,
                            align_y=1,
                        ),
                        fill=rio.Color.TRANSPARENT,
                        ripple=True,
                        cursor=rio.CursorStyle.POINTER,
                    ),
                    on_press=self._on_toggle_open,
                ),
                width=9,
            ),
            # Display a calendar so the user can pick a date
            content=rio.Column(
                comps.Calendar(
                    value=self.bind().value,
                    on_change=self._on_value_change,
                    # Use a fresh calendar each time, so it displays the
                    # currently selected value each time the popup opens
                    key=str(random.random()),
                ),
                rio.Button(
                    "Cancel",
                    style="plain",
                    on_press=self._on_close,
                ),
                # spacing=0.5,
                margin=1,
            ),
            color="neutral",
            position="center",
            alignment=0.5,
            is_open=self._is_open,
        )
