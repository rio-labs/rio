from __future__ import annotations

# <additional-imports>
from datetime import datetime, timedelta

import rio

from .. import components as comps
from .. import theme

# </additional-imports>


# <component>
DATE_OPTIONS = [
    "Last 7 days",
    "Last 14 days",
    "Last 30 days",
    "Last 3 months",
    "Last 6 months",
    "Last year",
]


class StyledDateRectangle(rio.Component):
    """
    A component that represents a styled rectangle with date range and
    aggregation details.

    This component displays a rectangle containing text, start and end dates,
    and an aggregation level. It also supports an interactive state (e.g., open
    or closed) and handles user interactions.


    ## Attributes

    `start_date`: The starting date of the range.

    `end_date`: The ending date of the range.

    `aggregation`: The aggregation level for the date range.

    `text`: The text displayed inside the rectangle.

    `is_open`: Indicates whether the rectangle is in an open state.

    `_on_press`: An optional event handler triggered when the rectangle is pressed.
    """

    start_date: datetime
    end_date: datetime
    aggregation: str
    text: str
    is_open: bool

    _on_press: rio.EventHandler[[]] = None

    def on_press(self, _: rio.PointerEvent) -> None:
        """
        Handles the press event for the styled rectangle.

        This method updates the `start_date` and `aggregation` attributes based
        on the selected text value. The date range and aggregation level are
        determined by predefined options such as "Last 7 days", "Last 14 days",
        etc.
        """
        if self.text == "Last 7 days":
            self.start_date = self.end_date - timedelta(days=7)
            self.aggregation = "Daily"

        elif self.text == "Last 14 days":
            self.start_date = self.end_date - timedelta(days=14)
            self.aggregation = "Daily"

        elif self.text == "Last 30 days":
            self.start_date = self.end_date - timedelta(days=30)
            self.aggregation = "Daily"

        elif self.text == "Last 3 months":
            self.start_date = self.end_date - timedelta(days=90)
            self.aggregation = "Weekly"

        elif self.text == "Last 6 months":
            self.start_date = self.end_date - timedelta(days=180)
            self.aggregation = "Weekly"

        elif self.text == "Last year":
            self.start_date = self.end_date - timedelta(days=365)
            self.aggregation = "Monthly"

        self.is_open = False

    def build(self) -> rio.Component:
        return rio.PointerEventListener(
            rio.Rectangle(
                content=rio.Row(
                    rio.Text(
                        self.text,
                        style=theme.TEXT_STYLE_SMALL_BOLD,
                    ),
                    margin=0.5,
                    spacing=0.5,
                ),
                fill=rio.Color.TRANSPARENT,
                hover_fill=self.session.theme.background_color,
                corner_radius=self.session.theme.corner_radius_small,
                transition_time=0.1,
                cursor="pointer",
            ),
            on_press=self.on_press,
        )


class DateSelector(rio.Component):
    """
    A component that allows users to select a date range and aggregation level.

    This component provides an interactive interface for selecting start and end
    dates, as well as an aggregation level (e.g., "Daily", "Weekly"). It also
    supports toggling between open and closed states for additional interaction.


    ## Attributes

    `start_date`: The starting date of the selected range.

    `end_date`: The ending date of the selected range.

    `aggregation`: The aggregation level for the selected date range.

    `_is_open`: Indicates whether the date selector is in an open state.
    """

    start_date: datetime
    end_date: datetime
    aggregation: str

    _is_open: bool = False

    def _on_toggle(self, _: rio.PointerEvent) -> None:
        self._is_open = not self._is_open

    def on_start_date_change(self, ev: rio.DateChangeEvent) -> None:
        # Convert date to datetime at midnight
        self.start_date = datetime.combine(ev.value, datetime.min.time())

    def on_end_date_change(self, ev: rio.DateChangeEvent) -> None:
        # Convert date to datetime at midnight
        self.end_date = datetime.combine(ev.value, datetime.min.time())

    def build(self) -> rio.Component:
        # Format the dates and strip leading zeros
        start_date_str = self.start_date.strftime("%d %b, %Y").lstrip("0")
        end_date_str = self.end_date.strftime("%d %b, %Y").lstrip("0")

        # Format the date string
        date_range: str = f"{start_date_str} - {end_date_str}"

        # Create a column of date options
        date_options = rio.Column(margin_y=0.5, align_y=0, margin_top=2)

        # Add date options to the column
        for date_option in DATE_OPTIONS:
            date_options.add(
                StyledDateRectangle(
                    start_date=self.bind().start_date,
                    end_date=self.bind().end_date,
                    aggregation=self.bind().aggregation,
                    text=date_option,
                    is_open=self.bind()._is_open,
                ),
            )

        # Create a row of date options with a separator
        pop_up_options = rio.Row(
            date_options,
            rio.Separator(color=self.session.theme.neutral_color.brighter(0.2)),
            rio.Column(
                rio.Text(
                    "Start date",
                    justify="center",
                    style=theme.TEXT_STYLE_SMALL_BOLD,
                ),
                rio.Calendar(
                    self.start_date,
                    on_change=self.on_start_date_change,
                ),
                spacing=1,
                align_x=0.5,
            ),
            rio.Separator(
                color=self.session.theme.neutral_color.brighter(0.2),
            ),
            rio.Column(
                rio.Text(
                    "End date",
                    justify="center",
                    style=theme.TEXT_STYLE_SMALL_BOLD,
                ),
                rio.Calendar(
                    self.end_date,
                    on_change=self.on_end_date_change,
                ),
                spacing=1,
                margin_right=0.2,
                align_x=0.5,
            ),
            align_x=0,
            spacing=0.5,
            margin=theme.POPUP_INNER_MARGIN,
        )

        # Style the pop-up content
        pop_up_content = comps.PopupRectangle(
            content=pop_up_options,
            align_x=0,
            min_width=20,
        )

        return rio.Popup(
            anchor=rio.PointerEventListener(
                rio.Rectangle(
                    content=rio.Row(
                        rio.Text(
                            date_range,
                            style=theme.TEXT_STYLE_SMALL_BOLD,
                            selectable=False,
                            align_x=0.5,
                            align_y=0.5,
                        ),
                        rio.Icon("material/keyboard_arrow_down"),
                        spacing=0.5,
                        margin_y=0.3,
                        margin_x=0.6,
                    ),
                    fill=self.session.theme.background_color,
                    hover_fill=self.session.theme.neutral_color,
                    corner_radius=self.session.theme.corner_radius_small,
                    transition_time=0.1,
                ),
                on_press=self._on_toggle,
            ),
            content=pop_up_content,
            is_open=self.bind()._is_open,
            position="bottom",
            user_closable=True,
            align_x=0.5,
            align_y=0.5,
        )


# </component>
