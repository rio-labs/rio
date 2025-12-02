import dataclasses
import typing as t

import rio

from .component import AccessibilityRole, Component, Key

__all__ = ["TabItem", "Tabs"]


@dataclasses.dataclass(frozen=True)
class TabItem:
    """
    Represents a single tab in a Tabs component.

    This dataclass holds the title, content, and optional icon for a tab.

    ## Attributes

    `title`: The title of the tab.

    `content`: The content component shown when this tab is active.

    `icon`: The icon for the tab, or None for no icon.
    """

    title: str  # The title of the tab
    content: Component  # The content component shown when this tab is active
    icon: str | None = None  # The icon for the tab, or None for no icon


class Tabs(Component):
    """
    Displays a set of tabs, each with its own content.

    This component manages multiple TabItem objects and displays the content of
    the active tab.

    ## Attributes

    `tabs`: The sequence of TabItem objects representing each tab.

    `active_tab_index`: The index of the currently active tab.

    ## Metadata

    `experimental`: True
    """

    tabs: t.Sequence[TabItem]
    active_tab_index: int = 0

    if not t.TYPE_CHECKING:
        _children: list[Component] = []

    def __init__(
        self,
        *tabs: TabItem,
        active_tab_index: int = 0,
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

        self.tabs = tabs
        self.active_tab_index = active_tab_index

        self._children = [tab.content for tab in tabs]
        self._properties_set_by_creator_.add("_children")

    def build(self) -> Component:
        try:
            content = self.tabs[self.active_tab_index].content
        except IndexError:
            content = None

        return rio.Column(
            rio.SwitcherBar(
                *[
                    rio.SwitcherBarItem(index, tab.title, tab.icon)
                    for index, tab in enumerate(self.tabs)
                ],
                selected_value=self.bind().active_tab_index,
                align_x=0,
            ),
            rio.Switcher(content, grow_y=True),
        )
