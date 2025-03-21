from __future__ import annotations

import typing as t
from dataclasses import field

# <additional-imports>
import pandas as pd

import rio

from .. import components as comps
from .. import data_models, persistence

# </additional-imports>


# <component>
POLICY_TYPE_DATA: t.Tuple[list[str], list[int]] = (
    ["Home", "Car", "Travel", "Pet"],
    [769, 511, 384, 124],
)

CANCELLATION_REASON_DATA: t.Tuple[list[str], list[int]] = (
    ["Found Better Deal", "Sold Home", "Dissatisfied", "Sold Car"],
    [69, 46, 23, 23],
)


@rio.page(
    name="Sales Dashboard",
    url_segment="",
)
class SalesDashboardPage(rio.Component):
    """
    A responsive sales dashboard page displaying key performance metrics.

    Provides a comprehensive view of sales performance through:
    - Revenue tracking (line chart)
    - Top performers display
    - Key metrics (renewal and churn rates)
    - Policy type distribution (donut chart)
    - Sales performance table
    - Cancellation reasons (donut chart)


    ## Attributes:

    `sales_data`: The sales data to be displayed in the table.

    `revenue_df`: The revenue data to be displayed in the line chart.
    """

    # Initialize the sales data and revenue data as empty DataFrames to avoid
    # issues with the session not being populated yet.
    sales_data: pd.DataFrame = field(
        default_factory=lambda: pd.DataFrame(
            columns=[
                "employee",
                "calls booked",
                "sales won",
                "conversion rate",
                "outbound calls",
            ]
        )
    )
    revenue_df: pd.DataFrame = field(
        default_factory=lambda: pd.DataFrame(
            columns=["date", "sales", "target"]
        )
    )

    @rio.event.on_populate
    async def on_populate(self) -> None:
        self.sales_data = self.session[persistence.Persistence].sales_data
        self.revenue_df = self.session[persistence.Persistence].revenue_df

    def format_sales_data(self) -> pd.DataFrame:
        df = self.sales_data.copy()
        df.columns = [col.upper() for col in df.columns]
        df["SALES WON"] = df["SALES WON"].apply(lambda x: f"$ {x:,.0f}")
        df["CONVERSION RATE"] = (
            df["CONVERSION RATE"]
            .astype(float)
            .apply(lambda x: f"{x * 100:.0f}%")
        )
        return df.iloc[:10, :4]

    def calculate_grid_proportion(
        self,
        grid_width: int,
        columns: int = 7,
        row_spacing: int = 1,
    ) -> float:
        """
        Calculate the minimum width for a grid item based on the number of
        columns and row spacing. The grid width is a proportion of the total
        grid columns.

        Args:

        `grid_width`: The width of the grid item in columns.

        `columns`: The total number of columns in the grid.

        `row_spacing`: The spacing between rows in the grid.
        """
        margin = self.session[data_models.PageLayout].margin_app

        window_width = self.session.window_width

        min_width = (
            window_width - (margin * 2) - (columns - 1) * row_spacing
        ) / columns

        return min_width * grid_width

    def desktop_build(self) -> rio.Component:
        grid = rio.Grid(row_spacing=1, column_spacing=1, grow_y=True)
        layout = self.session[data_models.PageLayout]

        grid.add(
            comps.LineChartCard(
                header="Revenue",
                revenue=self.revenue_df,
                min_width=self.calculate_grid_proportion(2),
            ),
            row=0,
            column=0,
            width=2,
        )
        grid.add(
            comps.TopPerformers(
                sales_data=self.sales_data,
                min_width=self.calculate_grid_proportion(3),
            ),
            row=0,
            column=2,
            width=3,
        )

        grid.add(
            comps.RateCard(
                rate_topic="Renewal Rate",
                rate_level=0.82,
                min_width=self.calculate_grid_proportion(1),
            ),
            row=0,
            column=5,
        )

        grid.add(
            comps.RateCard(
                rate_topic="Churn Rate",
                rate_level=0.12,
                min_width=self.calculate_grid_proportion(1),
            ),
            row=0,
            column=6,
        )

        grid.add(
            comps.DonutChartCard(
                header="Policy Type",
                labels=POLICY_TYPE_DATA[0],
                values=POLICY_TYPE_DATA[1],
            ),
            row=1,
            column=0,
            width=2,
            height=2,
        )

        grid.add(
            rio.Card(
                rio.Table(data=self.format_sales_data(), margin=1),
            ),
            row=1,
            column=2,
            width=3,
            height=2,
        )

        grid.add(
            comps.DonutChartCard(
                header="Cancellation Reason",
                labels=CANCELLATION_REASON_DATA[0],
                values=CANCELLATION_REASON_DATA[1],
            ),
            row=1,
            column=5,
            width=2,
            height=2,
        )

        return rio.Column(
            rio.Text(
                "Sales Dashboard",
                font_size=2,
                font_weight="bold",
                grow_x=True,
                align_x=0.5,
            ),
            grid,
            margin_x=layout.margin_app,
            margin_y=2,
            spacing=2,
        )

    def mobile_build(self) -> rio.Component:
        layout = self.session[data_models.PageLayout]

        content_column = rio.Column(
            comps.LineChartCard(header="Revenue", revenue=self.revenue_df),
            comps.TopPerformers(sales_data=self.sales_data),
            comps.RateCard(
                rate_topic="Renewal Rate",
                rate_level=0.82,
            ),
            comps.RateCard(
                rate_topic="Churn Rate",
                rate_level=0.12,
            ),
            comps.DonutChartCard(
                header="Policy Type",
                labels=POLICY_TYPE_DATA[0],
                values=POLICY_TYPE_DATA[1],
            ),
            rio.Card(
                rio.ScrollContainer(
                    rio.Table(data=self.format_sales_data(), margin=1),
                    grow_y=True,
                    scroll_y="never",
                ),
            ),
            comps.DonutChartCard(
                header="Cancellation Reason",
                labels=CANCELLATION_REASON_DATA[0],
                values=CANCELLATION_REASON_DATA[1],
            ),
            spacing=1,
            align_y=0,
        )

        return rio.Column(
            rio.Text(
                "Sales Dashboard",
                font_size=2,
                font_weight="bold",
                grow_x=True,
                align_x=0.5,
            ),
            content_column,
            spacing=1,
            margin=layout.margin_app,
        )

    def build(self) -> rio.Component:
        """
        Decide which build method to use based on the device type.
        """
        layout = self.session[data_models.PageLayout]

        if layout.device == "desktop":
            return self.desktop_build()

        return self.mobile_build()


# </component>
