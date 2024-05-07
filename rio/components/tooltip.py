from __future__ import annotations

from typing import TYPE_CHECKING, Literal, final

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Tooltip",
]


@final
class Tooltip(FundamentalComponent):
    """
    A small pop-up window that appears when the user hovers over an element.

    `Tooltip` is a small pop-up window that appears when the user hovers over an
    element. It is commonly used to provide additional information about the
    element, such as a description or a hint.


    ## Attributes

    `anchor`: The component to which the tooltip is anchored.

    `tip`: The text or component to display in the tooltip.

    `position`: The position of the tooltip relative to the anchor. It can be
        one of the following values: `left`, `top`, `right`, `bottom`.


    ## Examples

    A minimal example of a `Tooltip` will be shown:

    ```python
    rio.Tooltip(
        anchor=rio.Icon("material/info"),
        tip="This is a tooltip.",
        position="top",
    )
    ```
    """

    anchor: rio.Component
    tip: str | rio.Component
    position: Literal["left", "top", "right", "bottom"]

    # Hide internal attributes from the IDE
    if not TYPE_CHECKING:
        _tip_component: rio.Component | None

    # Impute a Text instance if a string is passed in as the tip
    def __init__(
        self,
        anchor: rio.Component,
        tip: str | rio.Component,
        position: Literal["left", "top", "right", "bottom"],
        *,
        key: str | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        width: float | Literal["natural", "grow"] = "natural",
        height: float | Literal["natural", "grow"] = "natural",
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

        self.anchor = anchor
        self.tip = tip

        if isinstance(tip, str):
            self._tip_text = tip
            self._tip_component = None
        else:
            self._tip_text = None
            self._tip_component = tip

        self.position = position

        self._properties_set_by_creator_.add("_tip_component")

    def __post_init__(self):
        # FIXME: This breaks attribute bindings
        if isinstance(self._tip_text, str):
            self._tip_component = rio.Text(self._tip_text)


Tooltip._unique_id = "Tooltip-builtin"
