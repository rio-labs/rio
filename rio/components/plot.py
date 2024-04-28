from __future__ import annotations

import copy
import io
from typing import TYPE_CHECKING, Literal, cast, final

from uniserde import JsonDoc

import rio

from .. import maybes
from .fundamental_component import FundamentalComponent

if TYPE_CHECKING:
    import matplotlib.axes  # type: ignore
    import matplotlib.figure  # type: ignore
    import plotly.graph_objects  # type: ignore


__all__ = ["Plot"]


@final
class Plot(FundamentalComponent):
    """
    Displays a `matplotlib`, `seaborn` or `plotly` plot.


    ## Attributes

    `figure`: The plot figure to display.

    `background`: The background color of the plot. If `None`, a color from
        the theme is used.

    `corner_radius`: The corner radius of the plot


    ## Examples

    A minimal example with a plotly plot:

    ```python
    import plotly.graph_objects as go

    fig = go.Figure()

    # Create your own plot here (add traces, ect.)

    rio.Plot(fig)
    ```

    You can easily show plots defined in your build function by passing
    the figure to the `Plot` component.

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
            fig = px.line(df, x="x", y="y", title="sample figure")

            return rio.Plot(fig)
    ```
    """

    figure: (
        plotly.graph_objects.Figure
        | matplotlib.figure.Figure
        | matplotlib.axes.Axes
    )
    background: rio.Fill | None
    corner_radius: float | tuple[float, float, float, float] | None

    def __init__(
        self,
        figure: (
            plotly.graph_objects.Figure
            | matplotlib.figure.Figure
            | matplotlib.axes.Axes
        ),
        *,
        background: rio.FillLike | None = None,
        corner_radius: float | tuple[float, float, float, float] | None = None,
        key: str | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        width: Literal["natural", "grow"] | float = "natural",
        height: Literal["natural", "grow"] | float = "natural",
        align_x: float | None = None,
        align_y: float | None = None,
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
            width=width,
            height=height,
            align_x=align_x,
            align_y=align_y,
        )

        self.figure = figure
        self.background = (
            None if background is None else rio.Fill._try_from(background)
        )

        if corner_radius is None:
            self.corner_radius = self.session.theme.corner_radius_small
        else:
            self.corner_radius = corner_radius

    def _custom_serialize(self) -> JsonDoc:
        # Figure
        figure = self.figure
        plot: JsonDoc

        # Plotly
        if isinstance(figure, maybes.PLOTLY_GRAPH_TYPES):
            # Make the plot transparent, so `self.background` shines through.
            figure = cast("plotly.graph_objects.Figure", copy.copy(figure))
            figure.update_layout(
                {
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "paper_bgcolor": "rgba(0,0,0,0)",
                }
            )

            plot = {
                "type": "plotly",
                "json": figure.to_json(),
            }

        # Matplotlib (+ Seaborn)
        elif isinstance(figure, maybes.MATPLOTLIB_GRAPH_TYPES):
            if isinstance(figure, maybes.MATPLOTLIB_AXES_TYPES):
                figure = figure.figure

            figure = cast("matplotlib.figure.Figure", figure)

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


Plot._unique_id = "Plot-builtin"
