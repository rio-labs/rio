from __future__ import annotations

import io
import typing as t

from uniserde import JsonDoc

from .. import fills, maybes
from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

if t.TYPE_CHECKING:
    import matplotlib.axes  # type: ignore
    import matplotlib.figure  # type: ignore
    import plotly.graph_objects  # type: ignore


__all__ = ["Plot"]


@t.final
class Plot(FundamentalComponent):
    """
    Displays a `matplotlib`, `seaborn` or `plotly` plot.

    Plots are a very useful tool to visualize data. Not only that, but having
    a pretty graph in your app is a great way to make it more engaging and
    beautiful.

    Rio supports the most popular Python plotting libraries around: It can
    display plots made with `matplotlib`, `seaborn`, as well as `plotly`. Create
    a plot using the library of your choice and pass it to the `Plot` component
    to display it in your app.

    Plots created with `plotly` will be interactive when displayed in Rio. We
    recommend using it over the other options.

    ## Attributes

    `figure`: The plot figure to display.

    `background`: The background color of the plot. If `None`, a color from
        the theme is used.

    `corner_radius`: The corner radius of the plot


    ## Examples

    Here's a minimal example using a `plotly` plot. Using `plotly` is
    recommended, because the resulting plots are interactive.

    ```python
    import pandas as pd
    import plotly.express as px


    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            df = pd.DataFrame(
                {
                    "x": [1, 2, 3, 4],
                    "y": [4, 3, 2, 1],
                }
            )
            fig = px.line(
                df,
                x="x",
                y="y",
            )

            return rio.Plot(
                fig,
                # Set the size of the plot, because default is 0
                min_width=10,
                min_height=10,
                align_x=0.5,
                align_y=0.5,
            )
    ```

    Matplotlib plots are also supported:

    ```python
    import pandas as pd
    import matplotlib.pyplot as plt


    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            df = pd.DataFrame(
                {
                    "x": [1, 2, 3, 4],
                    "y": [4, 3, 2, 1],
                }
            )

            # Create a figure and add a plot to it
            fig = plt.figure()
            plt.plot(df)

            return rio.Plot(
                fig,
                # Set the size of the plot, because default is 0
                min_width=10,
                min_height=10,
                align_x=0.5,
                align_y=0.5,
            )
    ```

    As well as `seaborn` plots:

    ```python
    import pandas as pd
    import seaborn as sns


    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            df = pd.DataFrame(
                {
                    "x": [1, 2, 3, 4],
                    "y": [4, 3, 2, 1],
                }
            )
            fig = sns.lineplot(
                df,
                x="x",
                y="y",
            )

            return rio.Plot(
                fig,
                # Set the size of the plot, because default is 0
                min_width=10,
                min_height=10,
                align_x=0.5,
                align_y=0.5,
            )
    ```
    """

    figure: (
        plotly.graph_objects.Figure
        | matplotlib.figure.Figure
        | matplotlib.axes.Axes
    )
    background: fills._FillLike | None
    corner_radius: float | tuple[float, float, float, float] | None

    def __init__(
        self,
        figure: (
            plotly.graph_objects.Figure
            | matplotlib.figure.Figure
            | matplotlib.axes.Axes
        ),
        *,
        background: fills._FillLike | None = None,
        corner_radius: float | tuple[float, float, float, float] | None = None,
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
    ):
        super().__init__(
            key=key,
            margin=margin,
            margin_x=margin_x,
            margin_y=margin_y,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
            align_x=align_x,
            align_y=align_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
            accessibility_role=accessibility_role,
        )

        self.figure = figure
        self.background = background

        if corner_radius is None:
            self.corner_radius = self.session.theme.corner_radius_small
        else:
            self.corner_radius = corner_radius

    def _custom_serialize_(self) -> JsonDoc:
        # Figure
        figure = self.figure
        plot: JsonDoc

        # Plotly
        if isinstance(figure, maybes.PLOTLY_GRAPH_TYPES):
            # Make the plot transparent, so `self.background` shines through.
            figure = t.cast("plotly.graph_objects.Figure", figure)

            plot = {
                "type": "plotly",
                "json": figure.to_json(),
            }

        # Matplotlib (+ Seaborn)
        elif isinstance(figure, maybes.MATPLOTLIB_GRAPH_TYPES):
            # Seaborn "figures" are actually matplotlib `Axes` objects
            if isinstance(figure, maybes.MATPLOTLIB_AXES_TYPES):
                figure = figure.figure

            figure = t.cast("matplotlib.figure.Figure", figure)

            file = io.BytesIO()
            figure.savefig(
                file,
                format="svg",
                transparent=True,
                bbox_inches="tight",
            )

            plot = {
                "type": "matplotlib",
                "svg": bytes(file.getbuffer()).decode("utf-8"),
            }

        # Unsupported
        else:
            raise TypeError(f"Unsupported plot type: {type(figure)}")

        # Corner radius
        if isinstance(self.corner_radius, (int, float)):
            corner_radius = (self.corner_radius,) * 4
        else:
            corner_radius = self.corner_radius

        # Combine everything
        return {
            "plot": plot,
            "corner_radius": corner_radius,
        }


Plot._unique_id_ = "Plot-builtin"
