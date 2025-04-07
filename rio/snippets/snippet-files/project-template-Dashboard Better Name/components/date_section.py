from __future__ import annotations

# <additional-imports>
from datetime import datetime

import rio

from .. import components as comps

# </additional-imports>


# <component>
class DateSection(rio.Component):
    """
    A component that represents a date range section with aggregation options.

    This component allows users to specify a start date, an end date, and an aggregation
    level (e.g., "Daily", "Weekly", etc.). It also provides functionality to calculate
    aggregation options based on the selected date range.


    ## Attributes

    `start_date`: The starting date of the range.

    `end_date`: The ending date of the range.

    `aggregation`: The aggregation level for the date range. Defaults to
    "Daily".
    """

    start_date: datetime
    end_date: datetime
    aggregation: str = "Daily"

    def _calculate_aggregation_options(self) -> list[str]:
        # Calculate the length of time between start_date and end_date
        duration = (self.end_date - self.start_date).days

        # If the duration is greater than 30 days, add the option to aggregate
        # by week or month
        if duration > 30:
            return ["Weekly", "Monthly"]
        else:
            return ["Daily", "Weekly"]

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Row(
                comps.DateSelector(
                    start_date=self.bind().start_date,
                    end_date=self.bind().end_date,
                    aggregation=self.bind().aggregation,
                ),
                comps.SingleSelectDropdown(
                    label=self.aggregation,
                    options=self._calculate_aggregation_options(),
                    selected_value=self.bind().aggregation,
                ),
                align_x=0,
                spacing=1,
                margin=0.4,  # (1 - 0.6) Spacing of DateSelector
            ),
            rio.Separator(color=self.session.theme.neutral_color),
            align_y=0,
        )


# </component>
