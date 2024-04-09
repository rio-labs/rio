from dataclasses import field

import rio

# <additional-imports>
import pandas as pd
import plotly.graph_objs as go

# </additional-imports>


# <component>
class InteractivePlot(rio.Component):
    # The full dataset, containing all smartphone data. This will be loaded when
    # the component is initialized. See the `load_data` method for details.
    dataset: pd.DataFrame = field(default_factory=pd.DataFrame)

    # The currently selected columns to display in the scatterplot. These values
    # will be initializes when the dataset is loaded.
    x_axis: str = ""
    y_axis: str = ""

    # If this is `True`, we'll take care to remove unlikely data by keeping only
    # the tenth to ninetieth percentile of the dataset.
    remove_outliers: bool = False

    @rio.event.on_populate
    def load_data(self) -> None:
        self.dataset = pd.read_csv(
            self.session.assets / "smartphones.csv",
        )
        self.x_axis = self.dataset.columns[0]
        self.y_axis = self.dataset.columns[1]

    async def on_download_csv(self) -> None:
        # Build a CSV file from the selected columns
        selected_df = self.dataset[[self.x_axis, self.y_axis]]
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
        result = self.dataset

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
            df = self.dataset

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
