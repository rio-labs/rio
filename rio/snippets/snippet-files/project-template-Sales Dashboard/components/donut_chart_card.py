# <additional-imports>
import plotly.graph_objects as go

import rio

from .. import data_models

# </additional-imports>


# <component>
class DonutChartCard(rio.Component):
    """
    A card component that displays a donut chart showing the distribution of a
    given metric.


    ## Attributes:

    `header`: The header of the card.

    `labels`: The labels for the donut chart.

    `values`: The values for the donut chart.
    """

    header: str
    labels: list[str]
    values: list[int]

    def _create_donut_chart(self) -> rio.Component:
        """
        Create a donut chart showing the distribution.
        """
        # Get layout configuration from the session
        layout = self.session[data_models.PageLayout]

        # Assert color as rio.Color
        text_fill_color = self.session.theme.text_style.fill
        assert isinstance(text_fill_color, rio.Color)

        # Use `hole` to create a donut-like pie chart
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=self.labels,
                    values=self.values,
                    hole=0.6,
                )
            ]
        )

        fig.add_annotation(
            x=0.5,
            y=0.5,
            text=f'<span style="font-size:16px;font-weight:bold">Total</span><br><br><span style="font-size:20px;font-weight:bold">{sum(self.values):,.0f}</span>',
            font=dict(color=text_fill_color.as_plotly),
            showarrow=False,
        )

        # Add legend at the bottom
        fig.update_layout(
            template="plotly_dark",
            margin=dict(t=0, l=0, r=0, b=0, pad=0),  # Remove all margins
            legend=dict(
                orientation="h",  # horizontal orientation
                yanchor="bottom",
                y=-0.2,  # position below the chart
                xanchor="center",
                x=0.5,  # center horizontally
                font=dict(color=text_fill_color.as_plotly),
            ),
        )

        return rio.Plot(
            fig,
            grow_x=layout.grow_x_content,
            grow_y=layout.grow_y_content,
            min_height=layout.min_width_content,
            background=rio.Color.TRANSPARENT,
        )

    def build(self) -> rio.Component:
        return rio.Card(
            content=rio.Column(
                rio.Text(
                    self.header, font_size=2, font_weight="bold", grow_x=True
                ),
                rio.Text(
                    "February 2025",
                ),
                self._create_donut_chart(),
                spacing=1,
                margin=self.session[data_models.PageLayout].margin_in_card,
            ),
        )


# </component>
