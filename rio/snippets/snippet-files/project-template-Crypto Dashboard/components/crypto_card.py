from typing import *  # type:ignore

# <additional-imports>
import pandas as pd
import plotly.express as px

import rio

# </additional-imports>


# <component>
class CryptoCard(rio.Component):
    """
    The CryptoCard class is a component of a dashboard application, designed to handle
    and display cryptocurrency-related data. It uses the rio library to create
    interactive dashboard components and pandas DataFrame to store cryptocurrency data.

    The build method creates a rio.Card component that displays a line plot of the last
    50 data points of the cryptocurrency, the cryptocurrency's logo, the name and ticker
    symbol of the cryptocurrency, the amount of the cryptocurrency, and the amount of
    the cryptocurrency in USD. The layout of the card is a grid with 4 rows and 2 columns.

    If there is no data available for the cryptocurrency, a message is printed to the console.


    ## Attributes
        data: A pandas DataFrame that holds the cryptocurrency data.
        coin: A string representing the name of the cryptocurrency.
        coin_amount: A float representing the amount of the cryptocurrency.
        coin_ticker: A string representing the ticker symbol of the cryptocurrency.
        logo_url: A string representing the URL of the cryptocurrency's logo.

    ## Layout
    ```
    ╔══════════════════ CARD ════════════════════╗
    ║ ┏━━━━━━━━━━━━━┳━━ GRID ━━━━━━━━━━━━━━━━━━┓ ║
    ║ ┃             ┃                          ┃ ║
    ║ ┃ Image       ┃ Plot                     ┃ ║
    ║ ┃             ┃                          ┃ ║
    ║ ┣━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━┫ ║
    ║ ┃ Coin Ticker ┃ Coin Amount              ┃ ║
    ║ ┣━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━┫ ║
    ║ ┃ Coin Name   ┃ Coin Amount in USD       ┃ ║
    ║ ┗━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
    ╚════════════════════════════════════════════╝
    ```
    """

    data: pd.DataFrame
    coin: str
    coin_amount: float
    coin_ticker: str
    color: str
    logo_url: str

    def build(self) -> rio.Component:
        fig = px.line(
            self.data[self.coin].iloc[-50:],
            color_discrete_sequence=[self.color],
            height=200,
            width=200,
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

        grid = rio.Grid(
            column_spacing=0.5,
            row_spacing=1,
            margin=2,
        )

        # Create a grid layout for the card
        # The grid will have 4 rows and 2 columns
        # Because the width of the plot is bigger, the second column will be wider
        # like shown below:

        ############################################
        # Icon        | Plot                       #
        # Icon        | Plot                       #
        # Coin Ticker | Coin Amount                #
        # Coin Name   | Coin Amount in USD         #
        ############################################

        # Image with grid height 2
        grid.add(
            rio.Image(
                rio.URL(
                    self.logo_url
                ),  # logo_url = e.g. "https://cryptologos.cc/logos/bitcoin-btc-logo.svg?v=029"
                height=2,
                width=2,
                align_y=0.5,
            ),
            row=0,
            column=0,
        )

        # Plot with grid height 2
        grid.add(
            rio.Plot(
                figure=fig,
                corner_radius=0,
                height=4,
                background=self.session.theme.neutral_color,
            ),
            row=0,
            column=1,
            height=2,
        )

        # Text with coin name and grid height 1
        grid.add(
            rio.Text(
                self.coin.capitalize(),
                style=rio.TextStyle(font_size=1.2, font_weight="bold"),
                align_x=0,
            ),
            row=2,
            column=0,
        )

        # Text with coin amount and grid height 1
        grid.add(
            rio.Text(
                f"{self.coin_amount:.6f} {self.coin_ticker}",
                align_x=0,
                style=rio.TextStyle(font_size=1.2, font_weight="bold"),
            ),
            row=2,
            column=1,
        )

        # Text with coin ticker and grid height 1
        grid.add(
            rio.Row(
                rio.Text(
                    self.coin_ticker,
                ),
                rio.Text(" / USD", style="dim"),
                align_x=0,
            ),
            row=3,
            column=0,
        )
        # Text with coin amount in USD and grid height 1
        usd_amount = self.coin_amount * self.data[self.coin].iloc[-1]
        grid.add(rio.Text(f"{usd_amount:,.2f} USD", align_x=0), row=3, column=1)

        return rio.Card(
            grid,
            height=13,
        )


# </component>
