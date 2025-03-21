import rio

# <additional-imports>
from .. import data_models

# </additional-imports>


# <component>
class StyledTransaction(rio.Component):
    """
    A component that visually represents a transaction in a styled format.

    This component displays details such as:
    - Transaction type (Buy/Sell) with corresponding icon.
    - The asset name and its ticker.
    - The amount transacted and the transaction date.


    ## Attributes:

    - `transaction`: The transaction data to be displayed.
    """

    transaction: data_models.Transaction

    def build(self) -> rio.Component:
        # Determine transaction type and set corresponding text and icon
        # Sell transaction
        if self.transaction.amount < 0:
            text = "Sell"
            icon = rio.Icon(
                "material/arrow_downward", min_height=2, min_width=2, margin=0.5
            )

        # Buy transaction
        else:
            text = "Buy"
            icon = rio.Icon(
                "material/arrow_upward", min_height=2, min_width=2, margin=0.5
            )

        # Construct the transaction row layout
        return rio.Row(
            # Left rectangle with icon and background
            rio.Rectangle(
                content=icon,
                fill=self.session.theme.primary_color.replace(opacity=0.1),
                corner_radius=9999,
                align_y=0.5,
            ),
            # Column with transaction text details
            rio.Column(
                rio.Text(
                    f"{text} {self.transaction.name}",
                    font_weight="bold",
                    overflow="ellipsize",
                ),
                rio.Text(
                    f"{self.transaction.ticker} / USD",
                    style="dim",
                    font_size=0.8,
                ),
                grow_x=True,
            ),
            # Column with amount and date details
            rio.Column(
                rio.Text(
                    f"{self.transaction.amount:.5f}",
                    font_weight="bold",
                    justify="right",
                ),
                rio.Text(
                    self.transaction.date.strftime("%b %#d, %Y %H:%M"),
                    style="dim",
                    font_size=0.8,
                    justify="right",
                ),
            ),
            spacing=1,
        )


# </component>
