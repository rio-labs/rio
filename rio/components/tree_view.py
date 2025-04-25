import dataclasses
import typing as t

from ..utils import EventHandler
from .component import Component, Key
from .list_view import ListView, ListViewSelectionChangeEvent
from .tree_items import _TreeItemBase

__all__ = ["TreeView", "TreeViewSelectionChangeEvent"]


@t.final
@dataclasses.dataclass
class TreeViewSelectionChangeEvent:
    """
    Event triggered when the selection in a `TreeView` changes.

    ## Attributes:
        `selected_items`: A list of keys of the currently selected items.
    """

    selected_items: list[Key]


class TreeView(Component):
    """
    A component that displays a hierarchical tree structure.

    `TreeView` is a convenient way to display nested data, such as a file system or organizational chart.
    The `TreeView` component uses its items, which are instances of `AbstractTreeItem` (e.g., `SimpleTreeItem`).
    Each item can have children, and the tree supports expand/collapse functionality
    as well as optional single or multiple selection.

    ## Attributes

    `root_items`: The top-level items to display in the tree.

    `selection_mode`: Determines the selection behavior: "none" (no selection),
        "single" (one item selectable), or "multiple" (multiple items selectable).
        Defaults to "none".

    `selected_items`: A list of keys of currently selected items. Defaults to an empty list.

    `on_selection_change`: Event handler triggered when the selection changes.

    `key`: A unique key for this component. If the key changes, the component will be destroyed
        and recreated. This is useful for components which maintain state across rebuilds.

    ## Examples

    This minimal example creates a simple tree with one root item and one child, with multiple selection enabled:

    ```python
    rio.TreeView(
        rio.SimpleTreeItem(
            "Root",
            key="root",
            children=[rio.SimpleTreeItem("Child", key="child")],
        ),
        selection_mode="multiple",
        selected_items=["root"],
        key="tree1",
    )
    ```

    For a more complex tree with dynamic content and event handling:

    ```python
    import functools

    class MyComponent(rio.Component):
        items: list[str] = ["Item 1", "Item 2"]

        def on_selection_change(self, event: rio.TreeViewSelectionChangeEvent) -> None:
            print(f"Selected items: {event.selected_items}")

        def build(self) -> rio.Component:
            root_items = [
                rio.SimpleTreeItem(
                    text=item,
                    key=item,
                    children=[rio.SimpleTreeItem(f"Sub-{item}", key=f"sub-{item}")]
                )
                for item in self.items
            ]
            return rio.TreeView(
                *root_items,
                selection_mode="multiple",
                on_selection_change=self.on_selection_change,
                key="dynamic_tree",
            )
    ```

    ## Metadata

    `experimental`: True
    """

    root_items: list[_TreeItemBase]
    selection_mode: t.Literal["none", "single", "multiple"] = "none"
    selected_items: list[Key] = []
    on_selection_change: EventHandler[TreeViewSelectionChangeEvent] = None

    def __init__(
        self,
        *root_items: _TreeItemBase,
        key: str | int | None = None,
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
        selection_mode: t.Literal["none", "single", "multiple"] = "none",
        selected_items: list[Key] | None = None,
        on_selection_change: EventHandler[TreeViewSelectionChangeEvent] = None,
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
        )
        self.root_items = list(root_items)
        self.selection_mode = selection_mode
        self.selected_items = [] if selected_items is None else selected_items
        self.on_selection_change = on_selection_change

    def build(self) -> Component:
        return ListView(
            *self.root_items,
            selection_mode=self.selection_mode,
            selected_items=self.bind().selected_items,
            on_selection_change=self._on_selection_change,
        )

    def _on_selection_change(self, event: ListViewSelectionChangeEvent) -> None:
        self.selected_items = event.selected_items

        if self.on_selection_change is not None:
            self.on_selection_change(
                TreeViewSelectionChangeEvent(event.selected_items)
            )
