import typing as t

from .component import Component
from .list_view import ListView
from .tree_items import AbstractTreeItem

__all__ = ["TreeView"]


class TreeView(Component):
    root_items: list[AbstractTreeItem]
    selection_mode: t.Literal["none", "single", "multiple"] = "none"
    selected_keys: list[str | int] = []

    def __init__(
        self,
        *root_items: AbstractTreeItem,
        selection_mode: t.Literal["none", "single", "multiple"] = "none",
        selected_keys: list[str | int] = None,
        key: str | int | None = None,
    ) -> None:
        super().__init__(key=key)
        self.root_items = list(root_items)
        self.selection_mode = selection_mode
        self.selected_keys = selected_keys or []

    def build(self) -> Component:
        return ListView(
            *self.root_items,
            selection_mode=self.selection_mode,
            selected_keys=self.selected_keys,
        )
