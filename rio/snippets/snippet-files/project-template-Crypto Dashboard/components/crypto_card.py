from __future__ import annotations

# <additional-imports>
import pandas as pd
import plotly.graph_objects as go

import rio

from .. import data_models

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

    `coin`: Information about the selected coin.
    """

    data: pd.DataFrame
    coin: data_models.Coin

    def create_plot(self) -> rio.Component:
        """
        Create a line plot of the last 50 data points of the cryptocurrency.
        """

        # create a line plot of the last 50 data points of the selected coin
        fig = go.Figure()

        # Calculate min_y before creating the trace
        min_y = self.data[self.coin.name].iloc[-50:].min() * 0.95

        fig.add_trace(
            go.Scatter(
                x=self.data.index[-50:],
                y=self.data[self.coin.name].iloc[-50:],
                line=dict(color=self.coin.color),
                hovertemplate='<span style="font-size: 20px; padding: 20px">$%{y:,.2f}</span><extra></extra>',
                fill="tonexty",
                fillgradient=dict(
                    type="vertical",
                    # color stops for the gradient fill, provide a list of
                    # tuples so we get an sub^tle from top to bottom
                    colorscale=[
                        (
                            0,  # Start at bottom
                            rio.Color.from_hex(self.coin.color)
                            .replace(opacity=0.0)
                            .as_plotly,
                        ),
                        (
                            0.75,  # First transition point
                            rio.Color.from_hex(self.coin.color)
                            .replace(opacity=0.00)
                            .as_plotly,
                        ),
                        (
                            0.9,  # Second transition point
                            rio.Color.from_hex(self.coin.color)
                            .replace(opacity=0.08)
                            .as_plotly,
                        ),
                        (
                            1,  # Top
                            rio.Color.from_hex(self.coin.color)
                            .replace(opacity=0.1)
                            .as_plotly,
                        ),
                    ],
                ),
            )
        )

        # Add a trace that defines the bottom of the fill area
        fig.add_trace(
            go.Scatter(
                x=self.data.index[-50:],
                y=[min_y] * len(self.data.index[-50:]),
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",  # Hide hover for this trace
            )
        )

        # Calculate the minimum y value and set the y-axis range
        y_range = [
            min_y * 0.95,
            self.data[self.coin.name].iloc[-50:].max() * 1.05,
        ]

        # hide and lock down axes
        fig.update_xaxes(visible=False, fixedrange=True)
        fig.update_yaxes(visible=False, fixedrange=True, range=y_range)

        # remove facet/subplot labels
        fig.update_layout(annotations=[], overwrite=True)

        # strip down the rest of the plot
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, l=0, b=0, r=0),
        )

        return rio.Plot(
            figure=fig,
            corner_radius=0,
            background=self.session.theme.neutral_color,
            align_x=1,
            min_width=8.4,
            min_height=3,
        )

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
            # Create a filled rectangle with the coin logo as content
            rio.Rectangle(
                content=rio.Image(
                    rio.URL(
                        self.coin.logo
                    ),  # logo_url = e.g. "https://cryptologos.cc/logos/bitcoin-btc-logo.svg?v=029"
                    min_height=2,
                    min_width=2,
                    align_y=0.5,
                    align_x=0,
                    margin=0.5,
                ),
                fill=rio.Color.from_hex(self.coin.color).replace(opacity=0.3),
                corner_radius=self.session.theme.corner_radius_small,
                align_x=0,
                align_y=0.5,
            ),
            row=0,
            column=0,
        )

        # Plot with grid height 2
        grid.add(
            self.create_plot(),
            row=0,
            column=1,
            height=2,
        )

        # Text with coin name and grid height 1
        grid.add(
            rio.Text(
                self.coin.name.capitalize(),
                font_size=self.session.theme.text_style.font_size * 1.2,
                font_weight="bold",
                align_x=0,
                min_width=6.5,
                overflow="ellipsize",
            ),
            row=2,
            column=0,
        )

        # Text with coin amount and grid height 1
        grid.add(
            rio.Text(
                f"{self.coin.quantity_owned:,.4f} {self.coin.ticker}",
                justify="right",
                font_size=self.session.theme.text_style.font_size * 1.2,
                font_weight="bold",
            ),
            row=2,
            column=1,
        )

        # Text with coin ticker and grid height 1
        grid.add(
            rio.Row(
                rio.Text(self.coin.ticker),
                rio.Text(" / USD", style="dim"),
                align_x=0,
            ),
            row=3,
            column=0,
        )
        # Text with coin amount in USD and grid height 1
        usd_amount = (
            self.coin.quantity_owned * self.data[self.coin.name].iloc[-1]
        )
        grid.add(
            rio.Text(
                f"{usd_amount:,.2f} USD",
                justify="right",
            ),
            row=3,
            column=1,
        )

        return rio.Card(
            grid,
            min_height=13,
        )


# </component>
