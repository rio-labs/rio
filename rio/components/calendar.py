from __future__ import annotations

import dataclasses
import typing as t
from datetime import date

import imy.docstrings
from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "DateChangeEvent",
    "Calendar",
]


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class DateChangeEvent:
    """
    Holds information regarding a date change event.

    This is a simple dataclass that stores useful information for when the user
    changes the date in a `Calendar` or `DateInput`. You'll typically receive
    this as argument in `on_change` events.

    ## Attributes

    `value`: The newly selected date.
    """

    value: date


class Calendar(FundamentalComponent):
    """
    Allows the user to pick a date from a calendar.

    Calendars are large components, that display one month at a time. The user
    can switch between months and years, and select a day from the displayed
    month.

    For a similar, but more compact component consider using `rio.DateInput`.


    ## Attributes

    `value`: The currently selected date.

    `is_sensitive`: Whether the calendar should respond to user input.

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
                rio.Calendar(
                    # In order to retrieve a value from the component, we'll
                    # use an attribute binding. This way our own value will
                    # be updated whenever the user changes the value.
                    value=self.bind().value,
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
            return rio.Calendar(
                value=self.value,
                on_change=self.on_value_change,
            )
    ```
    """

    value: date

    _: dataclasses.KW_ONLY

    is_sensitive: bool = True
    on_change: rio.EventHandler[DateChangeEvent] = None

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "selectedYear": self.value.year,
            "selectedMonth": self.value.month,
            "selectedDay": self.value.day,
            "monthNamesLong": self.session._month_names_long,
            "dayNamesLong": self.session._day_names_long,
            "firstDayOfWeek": self.session._first_day_of_week,
        }

    async def _on_message_(self, msg: t.Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg

        try:
            new_year = msg["year"]
            new_month = msg["month"]
            new_day = msg["day"]
        except KeyError:
            raise AssertionError(
                f"Frontend has sent a message with missing keys: {msg}"
            )

        # Build the new date, still looking out for invalid values
        try:
            self.value = date(new_year, new_month, new_day)
        except ValueError as e:
            raise AssertionError(
                f"The frontend has sent an invalid date: {new_year!r}-{new_month!r}-{new_day!r}"
            ) from e

        # Trigger the press event
        await self.call_event_handler(
            self.on_change,
            DateChangeEvent(self.value),
        )


Calendar._unique_id_ = "Calendar-builtin"
