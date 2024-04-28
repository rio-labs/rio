from __future__ import annotations

from typing import *  # type: ignore

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Overlay",
]


@final
class Overlay(FundamentalComponent):
    """
    Displays its child above all other components.

    The overlay component takes a single child component, and displays it above
    all other components on the page. The child will not scroll with the rest of
    the page and is exempt from layouting.

    Components inside of overlays are allocated the entire screen, and are
    themselves responsible for positioning themselves as required. You can
    easily achieve this using the child's `align_x` and `align_y` properties.


    ## Attributes

    `content`: The component to display in the overlay. It will take up the
        entire size of the screen, so make sure to use properties such as
        `align_x` and `align_y` to position it as needed.


    ## Examples

    A simple example will display an `Overlay` with the text "Hello, world!"
    centered on the screen:

    ```python
    rio.Overlay(
        rio.Text("Hello, world!"),
        align_x=0.5,
        align_y=0.5,
    )
    """

    content: rio.Component

    def __init__(
        self,
        content: rio.Component,
        *,
        key: str | None = None,
    ):
        # This component intentionally doesn't accept the typical layouting
        # parameters, as the underlying HTML `Overlay` element will force itself
        # to span the entire screen, ignoring them.

        super().__init__(key=key)

        self.content = content

    def _get_debug_details(self) -> dict[str, Any]:
        result = super()._get_debug_details()

        # Overlays intentionally remove a lot of common properties, because they
        # would behave in unexpected ways.
        del result["width"]
        del result["height"]
        del result["margin"]
        del result["margin_x"]
        del result["margin_y"]
        del result["margin_left"]
        del result["margin_top"]
        del result["margin_right"]
        del result["margin_bottom"]

        return result


Overlay._unique_id = "Overlay-builtin"
