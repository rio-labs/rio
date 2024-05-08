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

    You can build Components also in a functional-oriented way. Here we have
    two functions that create all sections of the balance card:
    - balance_section
    - bar_chart_section

    The build method combines these sections into a single `rio.Card` component,
    creating a complete balance component for the dashboard.

    ## Attributes

    `data`: Historical data of the fetched crypto coins.
    """

    data: pd.DataFrame

    def total_balance(self, idx: int) -> float:
        """
        Calculates the total amount of our portfolio in USD.

        This function iterates over the coins in MY_COINS, and for each coin, it
        multiplies the owned coin amount of our portfolio with the current USD
        exchange rate. The sum of our portfolio in USD will be returned.


        ## Parameters

        `idx`: The index at which to calculate the total balance.
        """

        total = 0

        for coin in data_models.MY_COINS:
            total += data_models.MY_COINS[coin][0] * self.data[coin].iloc[idx]

        return total

    def percentual_differance_balance(self) -> float:
        """
        Calculates percentual change of our portfolio.
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

        A section that displays the total balance and the percental difference
        in balance. The total balance is displayed in bold, and the percental
        difference is displayed in green if it's positive and in red if it's
        negative. The section is returned as a Column component.

        ```
        ╔════════════════════════ Column ════════════════════════╗
        ║ ┏━━━━━━━━━━━━━━━━━━━━━━━ Text ━━━━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ My Balance                                         ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┏━━━━━━━━━━━━━━━━━━━━━━━ Text ━━━━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ Total Balance                                      ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┏━━━━━━━━━━━━━━━━━━━━━━━━ Row ━━━━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ ┏━━━━━━━━ Text ━━━━━━━━┓  ┏━━━━━━━━ Text ━━━━━━━━┓ ┃ ║
        ║ ┃ ┃ e.g. 400,000 USD     ┃  ┃ e.g. (-0.09 %)       ┃ ┃ ║
        ║ ┃ ┗━━━━━━━━━━━━━━━━━━━━━━┛  ┗━━━━━━━━━━━━━━━━━━━━━━┛ ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ╚════════════════════════════════════════════════════════╝
        ```
        """

        return rio.Column(
            rio.Text(
                "My Balance",
                style=rio.TextStyle(font_size=1.2, font_weight="bold"),
                align_x=0,
                margin_bottom=1,
            ),
            rio.Text("Total Balance", style="dim", align_x=0),
            rio.Row(
                rio.Text(
                    f"{self.total_balance(idx=-1):,.2f} USD",
                    style=rio.TextStyle(font_size=1.2, font_weight="bold"),
                    align_x=0,
                ),
                rio.Text(
                    f"({self.percentual_differance_balance():.2f} %)",
                    style=rio.TextStyle(
                        fill=(
                            rio.Color.GREEN
                            if self.percentual_differance_balance() > 0
                            else rio.Color.RED
                        )
                    ),
                ),
                spacing=1,
            ),
            spacing=1,
            align_y=1,
        )

    def chart_section(self, name: str, color: str) -> rio.Component:
        """
        Creates a bar chart section for the dashboard.

        ## Parameters

        `name`: The name of the section.

        `color`: The color of the bars in the bar chart.

        ```
        ╔════════════════════════ Column ════════════════════════╗
        ║ ┏━━━━━━━━━━━━━━━━━━━━━━━ Plot ━━━━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ Bar Chart                                          ┃ ║
        ║ ┃                                                    ┃ ║
        ║ ┃                                                    ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┏━━━━━━━━━━━━━━━━━━━━━━━ Text ━━━━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ Income | Expenses                                  ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┏━━━━━━━━━━━━━━━━━━━━━━━ Text ━━━━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ e.g. 980,000.00 USD                                ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ╚════════════════════════════════════════════════════════╝
        ```
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
        """
        Returns a complete balance card component for the dashboard.

        The balance card component consists of three sections and seperators
        between them:
        - balance_section
        - chart_section

        The sections are combined into a single `rio.Card` component, which is
        returned as the final balance card component for the dashboard.

        ```
        ╔══════════════════════════════ Card ═════════════════════════════╗
        ║ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Row ━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ ┏ balance_section ┓ ║ ┏ chart_section ┓ ║ ┏ chart_section ┓ ┃ ║
        ║ ┃ ┃                 ┃ ║ ┃               ┃ ║ ┃               ┃ ┃ ║
        ║ ┃ ┗━━━━━━━━━━━━━━━━━┛ ║ ┗━━━━━━━━━━━━━━━┛ ║ ┗━━━━━━━━━━━━━━━┛ ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ╚═════════════════════════════════════════════════════════════════╝
        """

        return rio.Card(
            rio.Row(
                # 1. Section
                self.balance_section(),
                rio.Separator(),
                # 2. Section
                self.chart_section(name="Income", color="green"),
                rio.Separator(),
                self.chart_section(name="Expenses", color="red"),
                margin=1,
                spacing=4,
                align_x=0.5,
            ),
            height=13,
        )


# </component>
