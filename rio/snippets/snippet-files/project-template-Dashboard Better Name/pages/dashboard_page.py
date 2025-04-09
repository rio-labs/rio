from __future__ import annotations

# <additional-imports>
from datetime import datetime

import rio

from .. import components as comps
from .. import constants

# </additional-imports>


# <component>
@rio.page(
    name="Home",
    url_segment="",
)
class DashboardPage(rio.Component):
    """
    Represents the Dashboard page of the application.

    This page provides an overview of key metrics and data visualizations, allowing users to monitor
    performance and trends over a specified date range.


    ## Attributes:

    `start_date`: The start date for the data displayed on the dashboard.

    `end_date`: The end date for the data displayed on the dashboard.

    `aggregation`: The aggregation level for the data ("Daily", "Weekly" or
    "Monthly).
    """

    start_date: datetime = datetime.strptime("2024-12-07", "%Y-%m-%d")
    end_date: datetime = datetime.strptime("2024-12-21", "%Y-%m-%d")
    aggregation: str = "Daily"

    def build(self) -> rio.Component:
        return rio.Column(
            comps.HomeSection(),
            comps.DateSection(
                start_date=self.bind().start_date,
                end_date=self.bind().end_date,
                aggregation=self.bind().aggregation,
            ),
            # Display the revenue graph, recent sales, and top countries card in
            # a scrollable container, allowing users to view key metrics and
            # data visualizations.
            rio.ScrollContainer(
                rio.Column(
                    comps.RevenueGraph(
                        data=constants.daily_sales_data_df,
                        start_date=self.bind().start_date,
                        end_date=self.bind().end_date,
                        aggregation=self.bind().aggregation,
                    ),
                    rio.Row(
                        comps.RecentSales(),
                        comps.TopCountriesCard(),
                        spacing=2,
                        proportions=[1, 1],
                    ),
                    spacing=2,
                    margin=1,
                    align_y=0,
                ),
                # Allow the scroll container to grow vertically to use the
                # available space on the page.
                grow_y=True,
            ),
        )


# </component>
