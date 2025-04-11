# <additional-imports>
import pandas as pd

import rio

from .. import data_models

# </additional-imports>


# <component>
class StyledPortfolio(rio.Component):
    """
    A component that visually represents a styled portfolio for a single
    cryptocurrency, including the daily return, logo, and the current value in
    dollars.


    ## Attributes:

    `coin`: The cryptocurrency represented by this component.
    `history`: Historical price data for the cryptocurrency.
    """

    coin: data_models.Coin
    history: pd.Series

    def calculate_daily_return(self) -> float:
        """
        Calculates the daily return of the cryptocurrency based on the last 24
        hours of data.

        The historical data is assumed to have intervals of 4 hours, so 6 data
        points represent a day.
        """
        # Get the last 6 data points (4-hour intervals for the last 24 hours)
        last_day = self.history.iloc[-6:]

        # Small value to prevent division by zero
        epsilon = 0.000000001

        if not last_day.empty:
            # Add epsilon to avoid division by zero
            return (last_day.iloc[-1] - last_day.iloc[0] + epsilon) / (
                last_day.iloc[0] + epsilon
            )

        # Return 0 if data is insufficient
        return 0.0

    def build(self) -> rio.Component:
        # Calculate the daily return
        daily_return = self.calculate_daily_return()

        # Determine the color of the daily return text (green for positive, red
        # for negative)
        if daily_return > 0:
            daily_return_color = rio.Color.from_hex(
                "#00ff00"
            )  # Green for positive
        else:
            daily_return_color = rio.Color.from_hex(
                "#ff0000"
            )  # Red for negative

        return rio.Row(
            # Left rectangle with logo and background color
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
                fill=rio.Color.from_hex(self.coin.color).replace(opacity=0.3),
                corner_radius=self.session.theme.corner_radius_small,
                align_x=0,
                align_y=0.5,
            ),
            # Center column with the coin name and daily return
            rio.Column(
                # Display the coin name in bold and capitalized
                rio.Text(
                    self.coin.name.capitalize(),
                    font_weight="bold",
                ),
                # Display the daily return percentage with appropriate color
                rio.Text(
                    f"{daily_return * 100:.4f} %",  # TODO
                    font_size=self.session.theme.text_style.font_size * 0.8,
                    fill=daily_return_color,
                ),
            ),
            rio.Spacer(),
            # Display the current portfolio value in dollars.
            rio.Text(
                f"$ {self.coin.quantity_owned * self.history.iloc[-1]:,.2f}"
            ),
            spacing=1,
        )


# </component>
