# <additional-imports>
import pandas as pd

import rio

from .. import components as comps
from .. import constants

# </additional-imports>


# <component>
class PortfolioOverview(rio.Component):
    """
    A component that provides an overview of the user's portfolio.

    This includes:
    - A styled representation of each cryptocurrency in the portfolio.
    - Separators between portfolio items.
    - A header summarizing the portfolio.


    ## Attributes:

    `data`: A DataFrame containing historical data for all assets in the
        portfolio.
    """

    data: pd.DataFrame

    def build(self) -> rio.Component:
        # Create a column layout to hold portfolio items with spacing
        content = rio.Column(spacing=1)

        # Total number of cryptocurrencies in the portfolio
        total_transactions = len(constants.MY_PORTFOLIO)

        for i, coin in enumerate(constants.MY_PORTFOLIO):
            # Add a styled portfolio component for the current cryptocurrency
            content.add(
                comps.StyledPortfolio(coin=coin, history=self.data[coin.name])
            )

            # Add separator if not first or last item
            if i < total_transactions - 1:  # Skip last item
                content.add(rio.Separator())

        # Wrap the portfolio overview in a content card with a header
        return comps.ContentCard(
            header="My Portfolio",
            content=content,
        )


# </component>
