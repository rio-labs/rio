
import rio

# <additional-imports>
import plotly.graph_objects as go
import pandas as pd

from .. import data_models

# </additional-imports>


# <component>
class LineChartCard(rio.Component):
    """
    A card component that displays a line chart comparing actual vs target
    sales.


    ## Attributes:

    `header`: The header of the card.

    `revenue`: The revenue data to be used in the line chart. Contains the date,
    sales, and target columns.
    """

    header: str
    revenue: pd.DataFrame

    def _create_line_chart(self) -> rio.Component:
        """
        Create a line chart showing the cumulative sales and target sales.
        """
        # Get layout configuration from the session
        layout = self.session[data_models.PageLayout]

        text_fill_color = self.session.theme.text_style.fill
        assert isinstance(text_fill_color, rio.Color)

        # Create two traces for the line chart
        df = self.revenue.copy()

        # Calculate cumulative sums
        df["sales_cum"] = df["sales"].cumsum()
        df["target_cum"] = df["target"].cumsum()

        # Create the figure
        fig = go.Figure()

        # Add traces
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["sales_cum"],
                name="Actual Sales",
                line=dict(color="#2E93fA", width=2),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["target_cum"],
                name="Target Sales",
                line=dict(color="#FF4560", width=2, dash="dash"),
            )
        )

        # Update layout
        fig.update_layout(
            template="plotly_dark",
            margin=dict(t=0, l=0, r=0, b=0, pad=0),  # Remove margins
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(color=text_fill_color.as_plotly),
            ),
            xaxis=dict(
                showgrid=True, gridcolor="rgba(128, 128, 128, 0.2)", title=None
            ),
            yaxis=dict(
                showgrid=True, gridcolor="rgba(128, 128, 128, 0.2)", title=None
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
                    self.header,
                    font_size=2,
                    font_weight="bold",
                    grow_x=True,
                ),
                rio.Text("February 2025"),
                self._create_line_chart(),
                spacing=1,
                margin=self.session[data_models.PageLayout].margin_in_card,
            ),
        )


# </component>
