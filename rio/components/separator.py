from __future__ import annotations

import dataclasses
import typing as t

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Separator",
]


@t.final
class Separator(FundamentalComponent):
    """
    A line to separate content.

    `Separator` creates a horizontal or vertical line that can be used to
    separate content. You can optionally assign a color.

    It is generally preferable to separate components using whitespace over
    explicit separators. Whitespace tends to look cleaner, while separators can
    add clutter. Separators can still absolutely make sense though, so here they
    are!


    ## Attributes

    `color`: The color of the `Separator`. If `None`, the color will be
        determined by the theme.


    ## Examples

    This example will display a two text components separated by a line:

    ```python
    rio.Row(
        rio.Text("First"),
        rio.Separator(),
        rio.Text("Second"),
        spacing=0.5,
    )
    ```
    """

    _: dataclasses.KW_ONLY
    color: rio.Color | None = None


Separator._unique_id_ = "Separator-builtin"
