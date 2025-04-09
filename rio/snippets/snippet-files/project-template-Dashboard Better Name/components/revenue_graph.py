from __future__ import annotations

from datetime import datetime

# <additional-imports>
import pandas as pd
import plotly.graph_objects as go

import rio

from .. import theme

# </additional-imports>


# <component>
class RevenueGraph(rio.Component):
    """
    A component that displays a graph of the revenue over time.


    ## Attributes

    `data`: The data to be displayed in the graph.

    `start_date`: The start date for the data to be displayed.

    `end_date`: The end date for the data to be displayed.

    `aggregation`: The level of aggregation for the data: daily, weekly, or
    monthly.
    """

    data: pd.DataFrame
    start_date: datetime
    end_date: datetime
    aggregation: str

    def _slice_data(self) -> pd.DataFrame:
        """
        Slices and aggregates the data based on the specified date range and
        aggregation level.
        """
        df = self.data.copy()
        # Ensure 'Date' is in datetime format
        df["Date"] = pd.to_datetime(df["Date"])

        # Slice the data between the start and end date
        mask = (df["Date"] >= self.start_date) & (df["Date"] <= self.end_date)
        df = df.loc[mask]

        # Set 'Date' as the index for resampling
        df.set_index("Date", inplace=True, drop=False)

        # Aggregate the data based on the selected aggregation level: daily,
        # weekly, or monthly
        if self.aggregation == "Daily":
            df["Sales"] = df["Sales"].resample("D").sum()
        elif self.aggregation == "Weekly":
            df["Sales"] = (
                df["Sales"].resample("W", label="right", closed="right").sum()
            )
        elif self.aggregation == "Monthly":
            df["Sales"] = df["Sales"].resample("ME", label="right").sum()

        df = df.dropna()

        return df

    def _create_revenue_graph(self) -> rio.Component:
        """
        Creates a revenue graph based on the sliced and aggregated data.

        The graph displays the revenue over time, with a filled area under the
        curve to represent the sales. The hovertext displays the date and sales
        properly formatted.
        """
        # Initialize the figure
        fig = go.Figure()

        # Slice and aggregate the data
        df = self._slice_data()

        # Create formatted hover text
        df["HoverText"] = (
            df["Date"].dt.strftime("%d %b")
            + ": $"
            + df["Sales"].map("{:,.0f}".format)
        )

        # Add the sales line with filled area under the line
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Sales"],
                line_shape="spline",
                mode="lines",
                name="Sales",
                line=dict(color=self.session.theme.primary_color.as_plotly),
                fill="tozeroy",  # Fill to the x-axis (zero y)
                fillcolor=self.session.theme.primary_color.replace(
                    opacity=0.1
                ).as_plotly,
                text=df["HoverText"],  # Assign the formatted text
                hoverinfo="text",  # Use the 'text' for hover info
            )
        )

        # Determine the axis ranges based on the data
        x_min = df["Date"].min()
        x_max = df["Date"].max()
        y_min = 0  # Since the fill starts at zero
        original_y_max = df["Sales"].max()
        y_max = original_y_max * 1.05  # Increase y_max by 5%

        # Generate tick values: every date except first and last
        all_dates = df["Date"].tolist()
        if len(all_dates) > 2:
            tick_vals = all_dates[1:-1]  # Exclude first and last dates
        else:
            tick_vals = all_dates  # If only two dates, keep them

        # Update the layout to remove excess space, configure axes, and customize hover labels
        fig.update_layout(
            xaxis=dict(
                range=[x_min, x_max],  # Tight range for x-axis
                showline=True,  # Enable the x-axis line
                linecolor=self.session.theme.neutral_color.as_plotly,  # Set x-axis line color
                linewidth=2,  # Set line width
                showgrid=False,  # Hide x-axis grid lines
                ticks="outside",  # Position ticks outside
                ticklen=5,  # Length of ticks
                tickwidth=1,  # Width of ticks
                tickfont=dict(
                    color=self.session.theme.neutral_color.brighter(
                        0.1
                    ).as_plotly
                ),  # Set tick label color to neutral
                tickcolor=self.session.theme.neutral_color.as_plotly,  # Color of ticks to match x-axis line
                tickvals=tick_vals,  # Set custom tick values
                ticktext=[
                    tick.strftime("%d %b") for tick in tick_vals
                ],  # Format tick labels to "20 Nov"
            ),
            yaxis=dict(
                range=[y_min, y_max],  # Updated range for y-axis
                showticklabels=False,  # Hide y-axis labels
                ticks="",  # Remove y-axis ticks
                showgrid=False,  # Hide y-axis grid lines
                autorange=False,  # Disable autorange to use the specified range
            ),
            hoverlabel=dict(
                bgcolor=self.session.theme.background_color.as_plotly,
                font=dict(
                    color="white",
                    weight="bold",
                ),
                bordercolor=self.session.theme.neutral_color.brighter(
                    0.1
                ).as_plotly,  # Set border color to blue
                font_size=15,  # Optional: Adjust font size
            ),
            margin=dict(l=0, r=0, t=0, b=0),  # Remove all margins
            showlegend=False,  # Disable the legend
            template="plotly_dark",  # Use the dark theme
        )

        # Define the length of the small vertical lines (tick marks)
        tick_line_length = y_max  # Set to the new y_max

        # Add a small vertical line for each tick on the x-axis
        for tick in tick_vals:
            fig.add_shape(
                type="line",
                x0=tick,
                y0=0,
                x1=tick,
                y1=tick_line_length,
                line=dict(
                    color=self.session.theme.neutral_color.as_plotly,
                    width=1,
                    dash="solid",
                ),
                xref="x",
                yref="y",
                layer="below",  # Ensure the lines are rendered below the plot
            )

        return rio.Plot(
            fig,
            min_height=30,
            background=rio.Color.TRANSPARENT,
        )

    def get_formatted_sum(self) -> str:
        """
        Returns the total revenue for the specified date range in a formatted
        string.
        """
        data_slice = self.data.copy()
        # Ensure 'Date' is in datetime format
        data_slice["Date"] = pd.to_datetime(data_slice["Date"])

        # Slice the data between the start and end date
        mask = (data_slice["Date"] >= self.start_date) & (
            data_slice["Date"] <= self.end_date
        )
        data_slice = data_slice.loc[mask]

        return f"${data_slice['Sales'].sum():,}"

    def build(self) -> rio.Component:
        return rio.Rectangle(
            content=rio.Column(
                rio.Text(
                    "Revenue Over Time",
                    fill=theme.TEXT_FILL_DARKER,
                    margin_left=1,
                ),
                # Add the total revenue for the specified date range
                rio.Text(
                    text=self.get_formatted_sum(),
                    font_size=2,
                    font_weight="bold",
                    fill=theme.TEXT_FILL_BRIGHTER,
                    margin_left=1,
                ),
                # Add the revenue graph
                self._create_revenue_graph(),
                spacing=1,
                margin_y=1,
            ),
            fill=rio.Color.TRANSPARENT,
            stroke_color=self.session.theme.neutral_color,
            stroke_width=0.1,
            corner_radius=self.session.theme.corner_radius_medium,
        )


# </component>
