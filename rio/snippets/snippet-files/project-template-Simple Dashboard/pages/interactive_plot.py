import urllib.request
from pathlib import Path

import pandas as pd
import plotly.graph_objs as go

import rio

# Load the dataset
CSV_PATH = Path(__file__).parent / "smartphone-sales.csv"
CSV_URL = "https://TODO-real-url.com"

if not CSV_PATH.exists():
    with urllib.request.urlopen(CSV_URL) as response:
        CSV_PATH.write_bytes(response.read())

raw_df = pd.read_csv(CSV_PATH)
raw_df = raw_df.head(1000)


# <component>
class InteractivePlot(rio.Component):
    x_axis: str = raw_df.columns[0]
    y_axis: str = raw_df.columns[1]

    remove_outliers: bool = False

    async def on_download_csv(self) -> None:
        # Build a CSV file from the selected columns
        selected_df = raw_df[[self.x_axis, self.y_axis]]
        csv = selected_df.to_csv(index=False)

        # Save the file
        await self.session.save_file(
            file_name="scatter.csv",
            file_contents=csv,
        )

    def filter_data(self) -> pd.DataFrame:
        """
        Remove outliers from the dataset, by keeping only the tenth to ninetieth
        percentile.
        """
        result = raw_df

        # Remove outliers in the x-axis
        series = result[self.x_axis]

        if series.dtype in [int, float]:
            lower = series.quantile(0.10)
            upper = series.quantile(0.90)

            result = result[(series > lower) & (series < upper)]

        # Remove outliers in the y-axis
        series = result[self.y_axis]

        if series.dtype in [int, float]:
            lower = series.quantile(0.10)
            upper = series.quantile(0.90)

            result = result[(series > lower) & (series < upper)]

        return result

    def build(self) -> rio.Component:
        # Fetch the data
        if self.remove_outliers:
            df = self.filter_data()
        else:
            df = raw_df

        # Build the plot
        return rio.Row(
            rio.Plot(
                go.Figure(
                    go.Scatter(
                        x=df[self.x_axis],
                        y=df[self.y_axis],
                        mode="markers",
                    ),
                ),
                width="grow",
                height="grow",
                background=rio.Color.TRANSPARENT,
            ),
            rio.Card(
                rio.Column(
                    rio.Text(
                        "Data Sources",
                        style="heading3",
                    ),
                    rio.Dropdown(
                        label="X Axis",
                        options=list(df.columns),
                        selected_value=self.bind().x_axis,
                    ),
                    rio.Dropdown(
                        label="Y Axis",
                        options=list(df.columns),
                        selected_value=self.bind().y_axis,
                    ),
                    rio.Text(
                        "Filters",
                        style="heading3",
                    ),
                    rio.Row(
                        rio.Text("Remove Outliers"),
                        rio.Spacer(),
                        rio.Switch(
                            is_on=self.bind().remove_outliers,
                        ),
                    ),
                    rio.Spacer(),
                    rio.Button(
                        "Download CSV",
                        icon="material/download",
                        on_press=self.on_download_csv,
                    ),
                    spacing=0.8,
                    margin=1,
                ),
                margin=1,
            ),
        )


# </component>
