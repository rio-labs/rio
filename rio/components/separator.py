from __future__ import annotations

from dataclasses import KW_ONLY
from typing import *  # type: ignore

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Separator",
]


@final
class Separator(FundamentalComponent):
    """
    A line to separate content.

    `Separator` is a horizontal or vertical line that can be used to separate content. It
    can be styled with a color. By default, it is a thin line with a light gray
    color.


    ## Attributes

    `color`: The color of the `Separator`. If `None`, the color will be
        determined by the theme.


    ## Examples

    A minimal example of `Separator`:

    ```python
    rio.Separator()
    ```

    A separator is commonly used to separate content. For example, to separate
    two buttons:

    ```python
    rio.Row(
        rio.Button("First"),
        rio.Separator(),
        rio.Button("Second"),
        align_x=0.5,  # Only take up as much space as needed by the content
        spacing=1,
    )
    ```
    """

    _: KW_ONLY
    color: rio.Color | None = None


Separator._unique_id = "Separator-builtin"
