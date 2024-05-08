from typing import *  # type:ignore

# <additional-imports>
import pandas as pd
import plotly.express as px

import rio

# </additional-imports>


# <component>
class CryptoCard(rio.Component):
    """
    Handle and display cryptocurrency-related data.

    Show a card with a line plot of the last 50 data points of the
    cryptocurrency, the cryptocurrency's logo, the name and ticker symbol of the
    cryptocurrency, the amount of the cryptocurrency, and the amount of the
    cryptocurrency in USD.


    ## Attributes

    `data`: Historical data of the fetched crypto coins.

    `coin`: Name of the selected coin.

    `coin_amount`: Representing the amount of the selected coin.

    `coin_ticker`: Representing the ticker symbol of the cryptocurrency.

    `logo_url`: Representing the URL of the cryptocurrency's logo.
    """

    data: pd.DataFrame
    coin: str
    coin_amount: float
    coin_ticker: str
    color: str
    logo_url: str

    def build(self) -> rio.Component:
        """
        Create a card with a line plot of the last 50 data points of the
        cryptocurrency, the cryptocurrency's logo, the name and ticker symbol of
        the cryptocurrency, the amount of the cryptocurrency, and the amount of
        the cryptocurrency in USD.

        See the approx. layout below:
        ```
        ╔══════════════════════════════ Card ═════════════════════════════╗
        ║ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Grid ━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ ┏━━━━━━ Image ━━━━━┓ ┏━━━━━━━━━━━━━━ Plot ━━━━━━━━━━━━━━━━┓ ┃ ║
        ║ ┃ ┃ e.g. BTC Logo    ┃ ┃ e.g. line plot of BTC data         ┃ ┃ ║
        ║ ┃ ┃                  ┃ ┃                                    ┃ ┃ ║
        ║ ┃ ┃                  ┃ ┃                                    ┃ ┃ ║
        ║ ┃ ┃                  ┃ ┃                                    ┃ ┃ ║
        ║ ┃ ┗━━━━━━━━━━━━━━━━━━┛ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ┃ ║
        ║ ┃ ┏━━━━━━ Text ━━━━━━┓ ┏━━━━━━━━━━━━━━ Text ━━━━━━━━━━━━━━━━┓ ┃ ║
        ║ ┃ ┃ Coin Ticker      ┃ ┃ Coin Amount                        ┃ ┃ ║
        ║ ┃ ┗━━━━━━━━━━━━━━━━━━┛ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ┃ ║
        ║ ┃ ┏━━━━━━ Text ━━━━━━┓ ┏━━━━━━━━━━━━━━ Text ━━━━━━━━━━━━━━━━┓ ┃ ║
        ║ ┃ ┃ Coin Name        ┃ ┃ Coin Amount in USD                 ┃ ┃ ║
        ║ ┃ ┗━━━━━━━━━━━━━━━━━━┛ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ╚═════════════════════════════════════════════════════════════════╝
        ```
        """
        # create a line plot of the last 50 data points of the selected coin
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

        # create a grid layout for the card
        # The grid will have 4 rows and 3 columns
        # Because the width of the plot is bigger, we get a ratio of 2:1
        grid = rio.Grid(
            column_spacing=0.5,
            row_spacing=1,
            margin=2,
        )

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
