import rio

# <additional-imports>
from .. import data_models

# </additional-imports>


# <component>
class RateCard(rio.Component):
    """
    A card component that displays a metric with a circular progress indicator.

    Creates a card with a title, date, and circular progress indicator that
    changes color based on the rate level:

    - `danger` (red) for rates < 50%
    - `warning` (orange) for rates between 50-90%
    - `Success` (green) for rates >= 90%


    ## Attributes:

    `rate_topic`: The topic of the rate card.

    `rate_level`: The level of the rate card.
    """

    rate_topic: str
    rate_level: float

    def build(self) -> rio.Component:
        # Get layout configuration from the session
        layout = self.session[data_models.PageLayout]

        if self.rate_level < 0.5:
            fill_color = self.session.theme.danger_color
            progress_color = self.session.theme.danger_palette.foreground
        elif self.rate_level < 0.9:
            fill_color = self.session.theme.warning_color
            progress_color = self.session.theme.warning_palette.foreground
        else:
            fill_color = self.session.theme.success_color
            progress_color = self.session.theme.success_palette.foreground

        return rio.Card(
            rio.Column(
                rio.Text(
                    self.rate_topic,
                    font_size=2,
                    font_weight="bold",
                ),
                rio.Text(
                    "February 2025",
                ),
                rio.Stack(
                    rio.ProgressCircle(
                        progress=1,
                        color=rio.Color.WHITE.replace(opacity=0.5),
                    ),
                    rio.ProgressCircle(
                        progress=self.rate_level,
                        color=progress_color,
                    ),
                    rio.Text(
                        f"{self.rate_level:.0%}",
                        align_x=0.5,
                        font_size=2,
                        font_weight="bold",
                    ),
                    # Let the stack grow in the y direction, so it is taking up
                    # the remaining space in the column.
                    grow_y=layout.grow_y_content,
                    min_height=layout.min_width_content,
                ),
                margin=layout.margin_in_card,
            ),
            color=fill_color,
        )


# </component>
