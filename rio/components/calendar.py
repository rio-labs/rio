from __future__ import annotations

import calendar
from dataclasses import KW_ONLY, dataclass
from datetime import date
from typing import final

import rio.docs

from .component import Component

__all__ = [
    "DateChangeEvent",
    "Calendar",
]


@final
@rio.docs.mark_constructor_as_private
@dataclass
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


class Calendar(Component):
    """
    Allows the user to pick a date from a calendar.

    Calendars are large components, that display one month at a time. The user
    can switch between months and years, and select a day from the displayed
    month.

    For a similar, but more compact component consider using `rio.DateInput`.

    ## Attributes

    `value`: The currently selected date.

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

    _: KW_ONLY
    on_change: rio.EventHandler[DateChangeEvent] = None

    _displayed_month: int = -1
    _displayed_year: int = -1

    def __post_init__(self) -> None:
        self._displayed_month = self.value.month
        self._displayed_year = self.value.year

    def _on_switch_to_previous_month(self) -> None:
        self._displayed_month -= 1

        if self._displayed_month == 0:
            self._displayed_month = 12
            self._displayed_year -= 1

    def _on_switch_to_next_month(self) -> None:
        self._displayed_month += 1

        if self._displayed_month == 12:
            self._displayed_month = 1
            self._displayed_year += 1

    def _on_switch_to_previous_year(self) -> None:
        self._displayed_year -= 1

    def _on_switch_to_next_year(self) -> None:
        self._displayed_year += 1

    async def _on_select_day(self, day: int) -> None:
        # Switch to the selected day
        self.value = date(
            self._displayed_year,
            self._displayed_month,
            day,
        )

        # Trigger the event handler
        await self.call_event_handler(
            self.on_change,
            DateChangeEvent(self.value),
        )

    def build(self) -> rio.Component:
        result = rio.Grid(
            row_spacing=0.2,
            column_spacing=0.2,
        )

        # Allow switching between months and years
        result.add(
            rio.IconButton(
                icon="material/keyboard-double-arrow-left",
                style="plain",
                on_press=self._on_switch_to_previous_year,
                size=1.8,
            ),
            0,
            0,
        )

        result.add(
            rio.IconButton(
                icon="material/keyboard-arrow-left",
                style="plain",
                on_press=self._on_switch_to_previous_month,
                size=1.8,
            ),
            0,
            1,
        )

        result.add(
            rio.Text(
                date(self._displayed_year, self._displayed_month, 1).strftime(
                    "%B %Y"
                ),
                width="grow",
            ),
            0,
            2,
            width=3,
        )

        result.add(
            rio.IconButton(
                icon="material/keyboard-arrow-right",
                style="plain",
                on_press=self._on_switch_to_next_month,
                size=1.8,
            ),
            0,
            5,
        )

        result.add(
            rio.IconButton(
                icon="material/keyboard-double-arrow-right",
                style="plain",
                on_press=self._on_switch_to_next_year,
                size=1.8,
            ),
            0,
            6,
        )

        # Leave some space
        result.add(
            rio.Spacer(height=0.5),
            1,
            0,
        )

        # Label the days of week
        week_names_short = [
            # Don't crash on empty values (these are client-supplied!)
            val[:1].upper()
            for val in self.session._day_names_long
        ]

        day_of_week_style = rio.TextStyle(
            font_weight="bold",
        )

        for ii in range(7):
            result.add(
                rio.Text(
                    week_names_short[
                        (ii + self.session._first_day_of_week) % 7
                    ],
                    style=day_of_week_style,
                ),
                2,
                ii,
            )

        # Add the individual days
        day_shift = date(
            self._displayed_year, self._displayed_month, 1
        ).weekday()
        day_shift = (day_shift - self.session._first_day_of_week + 6) % 7

        def add_for_day(content: rio.Component, day: int) -> None:
            """
            Adds the given component into the grid, at the correct location for
            the given day. One-indexed.
            """
            linear_index = day + day_shift

            result.add(
                content,
                linear_index // 7 + 4,
                linear_index % 7,
            )

        days_in_month = calendar.monthrange(
            self._displayed_year, self._displayed_month
        )[1]

        for ii in range(1, days_in_month + 1):
            is_selected_day = (
                ii == self.value.day
                and self._displayed_month == self.value.month
                and self._displayed_year == self.value.year
            )

            add_for_day(
                rio.MouseEventListener(
                    rio.Rectangle(
                        content=rio.Text(
                            str(ii),
                            selectable=False,
                        ),
                        fill=self.session.theme.primary_color
                        if is_selected_day
                        else rio.Color.TRANSPARENT,
                        corner_radius=99999,
                        ripple=True,
                        cursor=rio.CursorStyle.POINTER,
                        hover_fill=None
                        if is_selected_day
                        else self.session.theme.primary_color.replace(
                            opacity=0.2
                        ),
                        transition_time=0.1,
                        width=2.1,
                        height=2.1,
                    ),
                    on_press=lambda _, ii=ii: self._on_select_day(ii),
                ),
                ii,
            )

        return result
