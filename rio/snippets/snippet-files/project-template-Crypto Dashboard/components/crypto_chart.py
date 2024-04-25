from typing import *  # type:ignore

# <additional-imports>
import pandas as pd
import plotly.express as px

import rio

from .. import data_models

# </additional-imports>


# <component>
class CryptoChart(rio.Component):
    """
    The CryptoChart class is a component of a dashboard application, designed to
    handle and display cryptocurrency-related data.


    ## Attributes
        data: A pandas DataFrame that holds the cryptocurrency data.
        coin: A string representing the name of the cryptocurrency.
        logo_url: A string representing the URL of the cryptocurrency's logo.
        color: A string representing the color of the cryptocurrency's logo.

    ## Layout
    ```
    ╔═══════════════════ CARD ═══════════════════╗
    ║ ┏━━━━━━━━━━━━━━┳━━ Row ━━━━━━┳━━━━━━━━━━━┓ ║
    ║ ┃ Image        ┃ Coin Name   ┃ Dropdown  ┃ ║
    ║ ┣━━━━━━━━━━━━━━┻━━━━━━━━━━━━━┻━━━━━━━━━━━┫ ║
    ║ ┃ Plot                                   ┃ ║
    ║ ┃                                        ┃ ║
    ║ ┃                                        ┃ ║
    ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
    ╚════════════════════════════════════════════╝
    ```
    """

    data: pd.DataFrame
    coin: str
    logo_url: str = data_models.MY_COINS["bitcoin"][3]
    color: str = data_models.MY_COINS["bitcoin"][2]

    def on_change_coin(self, ev: rio.DropdownChangeEvent) -> None:
        """
        Handles the event of changing the selected coin.

        This function updates the coin, color and logo_url attributes based on the selected coin.

        ## Parameters
        ev (rio.DropdownChangeEvent): The event object containing the selected coin value.
        """
        self.coin = ev.value
        self.color = data_models.MY_COINS[self.coin][2]
        self.logo_url = data_models.MY_COINS[self.coin][3]

    def build(self) -> rio.Component:
        """
        Creates a Card component with the selected coin's line plot, logo, name, and dropdown.

        This function creates a line plot of the last 50 data points of the selected coin,
        using the plotly express library. The plot is displayed in a Plot component from the
        rio library. The Card component includes the coin's logo, name, and dropdown, as well
        as the line plot.

        Returns:
            rio.Card: A Card component with the selected coin's line plot, logo, name, and dropdown.
                See the layout below:

        """

        fig = px.line(
            self.data[self.coin].iloc[-50:],
            color_discrete_sequence=[self.color],
            height=200,
            width=200,
        )

        # Set x-axis labels to horizontal and remove labels
        fig.update_xaxes(tickangle=0, title_text="")
        fig.update_yaxes(title_text="")

        # strip down the rest of the plot
        fig.update_layout(
            showlegend=False,
            margin=dict(t=10, l=10, b=10, r=10),
        )

        return rio.Card(
            rio.Column(
                rio.Row(
                    rio.Image(
                        rio.URL(self.logo_url),
                        height=2,
                        width=2,
                    ),
                    rio.Text(
                        self.coin.capitalize(),
                        style=rio.TextStyle(font_size=1.2, font_weight="bold"),
                    ),
                    rio.Dropdown(
                        options={
                            value[1]: key
                            for key, value in data_models.MY_COINS.items()
                        },
                        on_change=self.on_change_coin,
                    ),
                    spacing=1,
                    align_x=0.1,
                ),
                rio.Plot(
                    figure=fig,
                    corner_radius=0,
                    height=20,
                    width=10,
                    background=self.session.theme.neutral_color,
                    # margin=1,
                ),
                spacing=1,
                align_y=0.5,
                margin=2,
            ),
        )


# </component>
