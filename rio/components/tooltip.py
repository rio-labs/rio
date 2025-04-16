from __future__ import annotations

import typing as t

import rio

from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = [
    "Tooltip",
]


@t.final
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

    `gap`: The distance between the tooltip and its anchor.


    ## Examples

    This example will display a label for an icon when the user hovers over it:

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
    position: t.Literal["auto", "left", "top", "right", "bottom"]
    gap: float

    # Hide internal attributes from the IDE
    if not t.TYPE_CHECKING:
        _tip_component: rio.Component | None

    # Impute a Text instance if a string is passed in as the tip
    def __init__(
        self,
        anchor: rio.Component,
        tip: str | rio.Component,
        position: t.Literal["auto", "left", "top", "right", "bottom"] = "auto",
        *,
        gap: float = 0.5,
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
        accessibility_role: AccessibilityRole | None = "tooltip",
    ) -> None:
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

        self.anchor = anchor
        self.tip = tip

        if isinstance(tip, str):
            self._tip_text = tip
            self._tip_component = None
        else:
            self._tip_text = None
            self._tip_component = tip

        self.position = position
        self.gap = gap

        self._properties_set_by_creator_.add("_tip_component")

    def __post_init__(self) -> None:
        # TODO: This breaks attribute bindings
        if isinstance(self._tip_text, str):
            self._tip_component = rio.Text(
                self._tip_text,
                selectable=False,
            )


Tooltip._unique_id_ = "Tooltip-builtin"
