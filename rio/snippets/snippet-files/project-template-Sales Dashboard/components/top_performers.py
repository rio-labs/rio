# <additional-imports>
import pandas as pd

import rio

from .. import data_models

# </additional-imports>


# <component>
class TopPerformerInfo(rio.Component):
    """
    Displays information about a top performing salesperson.

    Creates a styled card showing the performer's rank (1-3) with medal colors,
    profile picture, name and sales amount. Uses different colors for rankings:
    gold for 1st, silver for 2nd, and bronze for 3rd.


    ## Attributes:

    `top_performer`:

    `ranking`: Ranking of the top performer.
    """

    top_performer: pd.Series
    ranking: int

    def build(self) -> rio.Component:
        # Define the stroke color based on the ranking
        if self.ranking == 1:
            # Gold stroke color
            stroke_color = rio.Color.from_hex("#FFD700")
        elif self.ranking == 2:
            # Silver stroke color
            stroke_color = rio.Color.from_hex("#C0C0C0")
        else:
            # Bronze stroke color
            stroke_color = rio.Color.from_hex("#CD7F32")

        return rio.Column(
            rio.Stack(
                rio.Rectangle(
                    fill=rio.ImageFill(
                        self.session.assets
                        / f"top_performer_{self.ranking}.png"
                    ),
                    corner_radius=9999,
                    stroke_color=stroke_color,
                    stroke_width=0.3,
                    align_x=0.5,
                    align_y=0.5,
                    min_height=7,
                    min_width=7,
                    margin_bottom=0.75,
                ),
                rio.Rectangle(
                    content=rio.Text(
                        f"{self.ranking}",
                        font_size=1,
                        font_weight="bold",
                        justify="center",
                        fill=self.session.theme.background_color,
                    ),
                    fill=stroke_color,
                    stroke_color=self.session.theme.neutral_color,
                    stroke_width=0.1,
                    corner_radius=9999,
                    min_height=1.5,
                    min_width=1.5,
                    align_x=0.5,
                    align_y=1,
                ),
            ),
            rio.Text(
                self.top_performer["employee"],
                justify="center",
                font_weight="bold",
                font_size=1.2,
            ),
            rio.Text(
                f"$ {self.top_performer['sales won']:,.0f}",
                justify="center",
                font_size=2,
                font_weight="bold",
            ),
            spacing=1,
        )


class TopPerformers(rio.Component):
    """
    Displays the top 3 sales performers.

    This component creates a responsive layout that shows the top performing
    salespeople based on their 'sales won' metric.


    ## Attributes:

    `sales_data`: Sales data to be used to determine the top performers.
    """

    sales_data: pd.DataFrame

    def _get_top_three_performers(self) -> pd.DataFrame:
        """
        Get the top three sales performers based on 'sales won' metric.
        """
        try:
            return self.sales_data.nlargest(3, "sales won")
        except (TypeError, KeyError):
            return self.sales_data

    def build(self) -> rio.Component:
        # Get layout configuration from the session
        layout = self.session[data_models.PageLayout]

        # Define the layout based on the window width, on smaller screens we use
        # a row layout and on larger screens we use a column layout
        if layout.device == "desktop":
            performer_row = rio.Row(
                spacing=1,
                align_y=0.5,
                grow_y=True,
            )
        else:
            performer_row = rio.Column(
                spacing=1,
            )

        # Add the top 3 performers based on sales won
        top_performers = self._get_top_three_performers()

        ranking = 1
        for _, performer in top_performers.iterrows():
            performer_row.add(
                TopPerformerInfo(top_performer=performer, ranking=ranking)
            )
            ranking += 1

        return rio.Card(
            content=rio.Column(
                rio.Text(
                    "Top Performers",
                    font_size=2,
                    font_weight="bold",
                    grow_x=True,
                ),
                rio.Text(
                    "February 2025",
                ),
                performer_row,
                spacing=1,
                margin=layout.margin_in_card,
            ),
        )


# </component>
