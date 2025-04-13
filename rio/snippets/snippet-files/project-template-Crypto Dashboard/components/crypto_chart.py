from __future__ import annotations

# <additional-imports>
import pandas as pd
import plotly.express as px

import rio

from .. import constants, data_models

# </additional-imports>


# <component>
class CryptoChart(rio.Component):
    """
    The CryptoChart class is a component of a dashboard application, designed to
    handle and display cryptocurrency-related data.


    ## Attributes

    `data`: Historical data of the fetched crypto coins.

    `coin`: Information about the selected coin.

    `horizon`: The time horizon for the chart.
    """

    data: pd.DataFrame
    coin: data_models.Coin = constants.MY_PORTFOLIO[0]  # Bitcoin as default

    horizon: int = 7

    def on_change_coin(self, ev: rio.DropdownChangeEvent) -> None:
        """
        Updates the coin, color and logo_url attributes based on
        the selected coin.

        ## Parameters

        `ev`: The event object containing the selected coin value.
        """
        # Find the coin object from MY_PORTFOLIO where name matches selected
        # value
        self.coin = next(
            coin for coin in constants.MY_PORTFOLIO if coin.name == ev.value
        )

    def build(self) -> rio.Component:
        """
        Creates a line plot of the last 50 data points of the selected coin.

        See the approx. layout below:
        ```
        ╔═════════════════════════════ CARD ══════════════════════════════╗
        ║ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━ Column ━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ ┏━━━━━━━━━━━━━━━━━━━━━━━━━ Row ━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ ┃ ║
        ║ ┃ ┃ ┏━━━━ Image ━━━━┓  ┏━━━━ Text ━━━━┓  ┏━━━ Dropdown ━━━┓ ┃ ┃ ║
        ║ ┃ ┃ ┃ url           ┃  ┃ str          ┃  ┃ dict           ┃ ┃ ┃ ║
        ║ ┃ ┃ ┗━━━━━━━━━━━━━━━┛  ┗━━━━━━━━━━━━━━┛  ┗━━━━━━━━━━━━━━━━┛ ┃ ┃ ║
        ║ ┃ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ┃ ║
        ║ ┃                                                             ┃ ║
        ║ ┃ ┏━━━━━━━━━━━━━━━━━━━━━━━━━ Plot ━━━━━━━━━━━━━━━━━━━━━━━━━━┓ ┃ ║
        ║ ┃ ┃                                                         ┃ ┃ ║
        ║ ┃ ┃ Plotly Express Figure                                   ┃ ┃ ║
        ║ ┃ ┃                                                         ┃ ┃ ║
        ║ ┃ ┃                                                         ┃ ┃ ║
        ║ ┃ ┃                                                         ┃ ┃ ║
        ║ ┃ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ╚═════════════════════════════════════════════════════════════════╝
        ```
        """
        # Get the device type from the session
        device = self.session[data_models.PageLayout].device

        # Set hovertemplate based on the time horizon
        if self.horizon == 1:
            hovertemplate = '<span style="font-size: 20px">$%{y:,.2f}</span><br>%{x|%b %-d, %H:%M}<extra></extra>'

        else:
            hovertemplate = '<span style="font-size: 20px">$%{y:,.2f}</span><br>%{x|%b %-d}<extra></extra>'

        # Create a line plot of the selected data points of the selected coin
        fig = px.line(
            self.data[self.coin.name].iloc[-self.horizon * 8 :],
            color_discrete_sequence=[self.coin.color],
        )

        # Make line thicker
        fig.update_traces(
            line=dict(width=3),
            hovertemplate=hovertemplate,
        )

        # Set x-axis labels to horizontal and remove labels
        fig.update_xaxes(
            tickangle=0,
            title_text="",
            tickfont=dict(color="white"),
        )
        fig.update_yaxes(
            title_text="",
            tickfont=dict(color="white"),
        )

        # strip down the rest of the plot
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, l=0, b=0, r=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
        )

        # Create Desktop view
        if device == "desktop":
            return rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Rectangle(
                            content=rio.Image(
                                rio.URL(
                                    self.coin.logo,
                                ),  # logo_url = e.g. "https://cryptologos.cc/logos/bitcoin-btc-logo.svg?v=029"
                                min_height=2,
                                min_width=2,
                                align_y=0.5,
                                align_x=0,
                                margin=0.5,
                            ),
                            fill=rio.Color.from_hex(self.coin.color).replace(
                                opacity=0.3
                            ),
                            corner_radius=self.session.theme.corner_radius_small,
                            align_x=0,
                            align_y=0.5,
                        ),
                        rio.Text(
                            self.coin.name.capitalize(),
                            font_size=self.session.theme.text_style.font_size
                            * 1.2,
                            font_weight="bold",
                            align_x=0,
                            min_width=7,
                        ),
                        rio.Dropdown(
                            options={
                                coin.ticker: coin.name
                                for coin in constants.MY_PORTFOLIO
                            },
                            on_change=self.on_change_coin,
                            align_y=0.5,
                        ),
                        # Add a spacer to fill up the remaining space
                        rio.Spacer(),
                        # Create a switcher bar to change the time horizon, if
                        # the user selects a different time horizon, the chart
                        # will automatically update
                        rio.SwitcherBar(
                            values=[1, 7, 30, 90],
                            names=["1D", "7D", "1M", "3M"],
                            selected_value=self.bind().horizon,
                        ),
                        spacing=1,
                    ),
                    rio.Plot(
                        figure=fig,
                        corner_radius=0,
                        min_height=20,
                        min_width=10,
                        background=self.session.theme.neutral_color,
                    ),
                    spacing=1,
                    align_y=0.5,
                    margin=2,
                ),
            )

        # Build Mobile view
        # Same game, slightly different layout, and smaller plot hight
        return rio.Card(
            rio.Column(
                rio.Row(
                    rio.Rectangle(
                        content=rio.Image(
                            rio.URL(
                                self.coin.logo,
                            ),  # logo_url = e.g. "https://cryptologos.cc/logos/bitcoin-btc-logo.svg?v=029"
                            min_height=2,
                            min_width=2,
                            align_y=0.5,
                            align_x=0,
                            margin=0.5,
                        ),
                        fill=rio.Color.from_hex(self.coin.color).replace(
                            opacity=0.3
                        ),
                        corner_radius=self.session.theme.corner_radius_small,
                        align_x=0,
                        align_y=0.5,
                    ),
                    rio.Text(
                        self.coin.name.capitalize(),
                        font_size=self.session.theme.text_style.font_size * 1.2,
                        font_weight="bold",
                        grow_x=True,
                        overflow="ellipsize",
                    ),
                    rio.Dropdown(
                        options={
                            coin.ticker: coin.name
                            for coin in constants.MY_PORTFOLIO
                        },
                        on_change=self.on_change_coin,
                        align_y=0.5,
                    ),
                    spacing=1,
                ),
                rio.SwitcherBar(
                    values=[1, 7, 30, 90],
                    names=["1D", "7D", "1M", "3M"],
                    selected_value=self.bind().horizon,
                ),
                rio.Plot(
                    figure=fig,
                    corner_radius=0,
                    min_height=15,
                    background=self.session.theme.neutral_color,
                ),
                spacing=1,
                align_y=0.5,
                margin=2,
            ),
        )


# </component>
