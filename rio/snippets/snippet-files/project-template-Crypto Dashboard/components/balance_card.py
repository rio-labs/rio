from typing import *  # type:ignore

# <additional-imports>
import pandas as pd
import plotly.express as px

import rio

from .. import data_models

# </additional-imports>


# <component>
class BalanceCard(rio.Component):
    """
    Displays information about the user's balance.

    The class provides methods to calculate total balance at a given index,
    calculate changes in recent balances, and create visual sections for the
    dashboard. These sections include a balance section displaying the total
    balance and the relative difference in balance, and a bar chart section
    displaying a bar chart with a given color and hidden axes.

    The build method combines these sections into a single `rio.Card` component,
    creating a complete balance component for the dashboard.

    ## Attributes

    `data`: A pandas DataFrame containing the data for the coins in MY_COINS.
    """

    data: pd.DataFrame

    def total_balance(self, idx: int) -> float:
        """
        Calculates the total balance for a given index.

        # LAUNCH-TODO: Balance in what?

        This function iterates over the coins in MY_COINS, and for each coin, it
        multiplies the coin's value by the value at the given index in the data
        for that coin. It then adds these products to a total and returns this
        total.

        Returns the total balance at the given index.

        ## Parameters

        `idx`: The index at which to calculate the total balance.
        """

        total = 0

        for coin in data_models.MY_COINS:
            total += data_models.MY_COINS[coin][0] * self.data[coin].iloc[idx]

        return total

    def percental_differance_balance(self) -> float:
        """
        Calculates the percental difference in balance between the last and
        second last balances.

        This function iterates over the coins in MY_COINS, and for each coin, it
        multiplies the coin's value by the total balance at the last and second
        last indices. It then calculates the percental difference between these
        two totals and returns this value.

        Returns the percental difference between the last and second last
        balances.
        """

        total_last = 0
        total_second_last = 0
        epsilon = 0.0000001

        for coin in data_models.MY_COINS:
            total_last += data_models.MY_COINS[coin][0] * self.total_balance(
                idx=-1
            )
            total_second_last += data_models.MY_COINS[coin][
                0
            ] * self.total_balance(idx=-2)

        # epsilon ensures that the denominator is never zero
        return (
            (total_last - total_second_last) / (total_second_last + epsilon)
        ) * 100

    def balance_section(self) -> rio.Component:
        """
        Creates a balance section for the dashboard.

        This function creates a section that displays the total balance and the
        percental difference in balance. The total balance is displayed in bold,
        and the percental difference is displayed in green if it's positive and
        in red if it's negative. The section is returned as a Column component
        from the rio library.

        Returns a Column component from the rio library, which includes the
        total balance, the percental difference in balance, and some text and
        spacing elements.
        """

        return rio.Column(
            rio.Text(
                "My Balance",
                style=rio.TextStyle(font_size=1.2, font_weight="bold"),
                align_x=0,
            ),
            rio.Spacer(height=1),
            rio.Text("Total Balance", style="dim", align_x=0),
            rio.Row(
                rio.Text(
                    f"{self.total_balance(idx=-1):,.2f} USD",
                    style=rio.TextStyle(font_size=1.2, font_weight="bold"),
                    align_x=0,
                ),
                rio.Text(
                    f"({self.percental_differance_balance():.2f} %)",
                    style=rio.TextStyle(
                        fill=(
                            rio.Color.GREEN
                            if self.percental_differance_balance() > 0
                            else rio.Color.RED
                        )
                    ),
                ),
                spacing=1,
            ),
            spacing=1,
            align_y=1,
        )

    def bar_chart_section(self, name: str, color: str) -> rio.Component:
        """
        Creates a bar chart section for the dashboard.

        This function creates a bar chart with the given color and hidden axes.
        The function returns a Column component from the rio library, which includes
        the Plot, the name of the section, and the total balance in USD.

        Returns a Column component from the rio library, which includes the
        Plot, the name of the section, and the total balance in USD.

        ## Parameters

        `name`: The name of the section.

        `color`: The color of the bars in the bar chart.
        """

        fig = px.bar(
            data_models.BAR_CHART,
            height=200,
            width=200,
            color_discrete_sequence=[color],
        )
        # hide and lock down axes
        fig.update_xaxes(visible=False, fixedrange=True)
        fig.update_yaxes(visible=False, fixedrange=True)
        # remove facet/subplot labels
        fig.update_layout(annotations=[], overwrite=True)

        # strip down the rest of the plot
        fig.update_layout(
            showlegend=False,
            margin=dict(t=10, l=10, b=10, r=10),
        )

        return rio.Column(
            rio.Plot(
                figure=fig,
                height=5,
                width=20,
                background=self.session.theme.neutral_color,
            ),
            rio.Text(name, style="dim", align_x=0),
            rio.Text(
                f"{self.total_balance(idx=-1):,.2f} USD",
                style=rio.TextStyle(font_size=1.2, font_weight="bold"),
                justify="left",
            ),
            spacing=1,
            align_y=1,
        )

    def build(self) -> rio.Component:
        return rio.Card(
            rio.Row(
                # 1. Section
                self.balance_section(),
                rio.Separator(),
                # 2. Section
                self.bar_chart_section(name="Income", color="green"),
                rio.Separator(),
                self.bar_chart_section(name="Expenses", color="red"),
                margin=1,
                spacing=4,
                align_x=0.5,
            ),
            height=13,
        )


# </component>
