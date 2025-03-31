import typing as t

from ..utils import EventHandler
from .component import Component
from .list_view import ListView, ListViewSelectionChangeEvent
from .tree_items import AbstractTreeItem

__all__ = ["TreeView"]


class TreeView(Component):
    root_items: list[AbstractTreeItem]
    selection_mode: t.Literal["none", "single", "multiple"] = "none"
    selected_items: list[str | int] = []
    on_selection_change: EventHandler[ListViewSelectionChangeEvent] = (None,)

    def __init__(
        self,
        *root_items: AbstractTreeItem,
        selection_mode: t.Literal["none", "single", "multiple"] = "none",
        selected_items: list[str | int] = None,
        on_selection_change: EventHandler[ListViewSelectionChangeEvent] = None,
        key: str | int | None = None,
    ) -> None:
        super().__init__(key=key)
        self.root_items = list(root_items)
        self.selection_mode = selection_mode
        self.selected_items = selected_items or []
        self.on_selection_change = on_selection_change

    def build(self) -> Component:
        return ListView(
            *self.root_items,
            selection_mode=self.selection_mode,
            selected_items=self.selected_items,
            on_selection_change=self._on_selection_change,
        )

    def _on_selection_change(self, event: ListViewSelectionChangeEvent) -> None:
        self.selected_items = event.selected_items
        if self.on_selection_change is not None:
            self.on_selection_change(event)
