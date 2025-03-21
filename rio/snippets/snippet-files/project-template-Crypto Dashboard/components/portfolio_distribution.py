# <additional-imports>
import pandas as pd
import plotly.graph_objects as go

import rio

from .. import components as comps
from .. import constants

# </additional-imports>


# <component>
class PortfolioDistribution(rio.Component):
    """
    A component that visualizes the user's portfolio distribution as a donut chart.


    ## Attributes:

    `data`: A DataFrame containing historical data for the portfolio assets.
    """

    data: pd.DataFrame

    def build(self) -> rio.Component:
        content = rio.Column()

        # Get labels and colors
        labels = [coin.name.capitalize() for coin in constants.MY_PORTFOLIO]
        colors = [coin.color for coin in constants.MY_PORTFOLIO]

        # Calculate the portfolio values in dollar terms
        values = [
            coin.quantity_owned * self.data[coin.name].iloc[-1]
            for coin in constants.MY_PORTFOLIO
        ]

        # Create donut chart
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.6,  # Makes it a donut chart
                    marker_colors=colors,
                    textinfo="percent",  # Show only percentages
                    hovertemplate="<b>%{label}</b><br>"
                    + "$%{value:,.0f}<br>"
                    + "<extra></extra>",  # Remove trace info
                )
            ]
        )

        # Update layout
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, l=0, b=0, r=0),
        )

        # Wrap the chart in a Rio Plot component
        content = rio.Column(
            rio.Plot(
                figure=fig,
                corner_radius=0,
                background=rio.Color.TRANSPARENT,
                min_width=20,
                min_height=20,
                align_x=0.5,
            ),
            rio.Text(
                "Almost 100% of your portfolio is in crypto!",
                font_weight="bold",
                justify="center",
                overflow="wrap",
            ),
            spacing=3,
            margin_top=1,
        )

        return comps.ContentCard(
            header="Portfolio Split",
            content=content,
        )


# </component>
