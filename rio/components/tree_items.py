import typing as t

import typing_extensions as te

from ..utils import EventHandler
from .component import Component
from .fundamental_component import FundamentalComponent
from .linear_containers import Column, Row
from .text import Text

__all__ = ["CustomTreeItem", "AbstractTreeItem", "SimpleTreeItem"]


@t.final
class CustomTreeItem(FundamentalComponent):
    """
    A fundamental tree item component with customizable content and optional children.

    `CustomTreeItem` is the core building block for tree structures in Rio. It supports a header
    with content, an optional expand button for toggling visibility of children, and a container
    for nested items. This component is typically used internally by `AbstractTreeItem` and its
    derivatives, but can be customized directly for advanced use cases.

    ## Attributes

    `content`: The primary content to display in the tree item.

    `expand_button`: An optional component (e.g., a Text icon) to toggle expansion. If provided
        and `children_container` is present, it becomes clickable.

    `children_container`: An optional container (e.g., Column) holding child tree items.

    `is_expanded`: Whether the children are currently visible. Defaults to False.

    `on_expansion_changed`: Event handler triggered when the expansion state changes.

    ## Examples

    This minimal example creates a simple tree item with custom content and no children:

    ```python
    rio.CustomTreeItem(
        content=rio.Text("Leaf Node"),
        key="leaf",
    )
    ```

    A more complex example with an expand button and nested children:

    ```python
    rio.CustomTreeItem(
        content=rio.Text("Parent Node"),
        expand_button=rio.Text("▶"),
        children_container=rio.Column(
            rio.CustomTreeItem(content=rio.Text("Child Node"), key="child"),
        ),
        is_expanded=False,
        on_expansion_changed=lambda expanded: print(f"Expanded: {expanded}"),
        key="parent",
    )
    ```
    """

    content: Component
    expand_button: Component | None = None
    children_container: Component | None = None
    is_expanded: bool = False
    on_expansion_changed: EventHandler[bool] = None

    def __init__(
        self,
        content: Component,
        *,
        key: str | int | None = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        expand_button: Component | None = None,
        children_container: Component | None = None,
        is_expanded: bool = False,
        on_expansion_changed: EventHandler[bool] = None,
    ) -> None:
        super().__init__(
            key=key,
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
        )
        self.content = content
        self.expand_button = expand_button
        self.children_container = children_container
        self.is_expanded = is_expanded
        self.on_expansion_changed = on_expansion_changed

    async def _on_message_(self, msg: t.Any) -> None:
        assert isinstance(msg, dict), f"Invalid message: {msg}"
        assert msg.get("type") == "toggleExpansion", (
            f"Invalid message type: {msg.get('type')}"
        )
        is_expanded = msg.get("is_expanded")
        assert isinstance(is_expanded, bool), (
            f"Invalid is_expanded: {is_expanded}"
        )
        self._apply_delta_state_from_frontend({"is_expanded": is_expanded})

        if self.on_expansion_changed:
            await self.call_event_handler(
                self.on_expansion_changed, is_expanded
            )
        await self.session._refresh()


CustomTreeItem._unique_id_ = "CustomTreeItem-builtin"


class AbstractTreeItem(Component):
    """
    An abstract base class for tree items with text and optional children.

    `AbstractTreeItem` provides a foundation for building tree items with a text label and
    nested children. It constructs a `CustomTreeItem` with an expand button and a container
    for children, which can be toggled visible or hidden. Subclasses like `SimpleTreeItem`
    can extend this to add more features.

    ## Attributes

    `text`: The primary text to display.

    `children`: A list of nested tree items (of the same type). Defaults to an empty list.

    `is_expanded`: Whether the children are visible. Defaults to False.

    `on_press`: Triggered when the item is pressed.

    `on_expansion_changed`: Triggered when the expansion state changes.

    ## Examples

    This minimal example creates a basic tree item with no children:

    ```python
    rio.AbstractTreeItem("Root Node", key="root")
    ```

    A tree item with nested children and event handling:

    ```python
    rio.AbstractTreeItem(
        text="Parent",
        key="parent",
        children=[rio.AbstractTreeItem("Child", key="child")],
        is_expanded=True,
        on_press=lambda: print("Pressed"),
        on_expansion_changed=lambda expanded: print(f"Expanded: {expanded}"),
    )
    ```
    """

    text: str
    children: list[te.Self] = []
    is_expanded: bool = False
    on_press: EventHandler[[]] = None
    on_expansion_changed: EventHandler[bool] = None

    def __init__(
        self,
        text: str,
        *,
        key: str | int | None = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        children: list[te.Self] | None = None,
        is_expanded: bool = False,
        on_press: EventHandler[[]] = None,
        on_expansion_changed: EventHandler[bool] = None,
    ) -> None:
        super().__init__(
            key=key,
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
        )
        self.text = text
        self.children = children or []
        self.is_expanded = is_expanded
        self.on_press = on_press
        self.on_expansion_changed = on_expansion_changed

    def build_content(self) -> Component:
        return Text(self.text, justify="left", selectable=False)

    def build(self) -> Component:
        expand_button = Text(
            ("▶" if not self.is_expanded else "▼") if self.children else "●",
            style="plain-text",
            key=f"expand_{self.key}",
        )
        if self.children:
            children_container = Column(
                *self.children,
                spacing=0.5,
                margin_left=1,
            )
        else:
            children_container = None

        return CustomTreeItem(
            expand_button=expand_button,
            content=self.build_content(),
            children_container=children_container,
            is_expanded=self.is_expanded,
            on_expansion_changed=self.on_expansion_changed,
            key="",
            min_width=self.min_width,
            min_height=self.min_height,
            grow_x=self.grow_x,
            grow_y=self.grow_y,
        )


class SimpleTreeItem(AbstractTreeItem):
    """
    A simple tree item with a header, optional secondary text, and children.

    `SimpleTreeItem` extends `AbstractTreeItem` to provide a convenient way to create tree items
    with additional features like secondary text and left/right children (e.g., icons or buttons).
    It’s ideal for most tree use cases, offering flexibility while maintaining simplicity.

    ## Attributes

    `text`: The primary text to display.

    `secondary_text`: Additional text to display below the primary text. This text may span
        multiple lines (use `"\\n"` to add a line break).

    `left_child`: A component to display on the left side of the item.

    `right_child`: A component to display on the right side of the item.

    `children`: A list of nested tree items. Defaults to an empty list.

    `is_expanded`: Whether the children are visible. Defaults to False.

    `on_press`: Triggered when the item is pressed.

    `on_expansion_changed`: Triggered when the expansion state changes.

    ## Examples

    This minimal example creates a simple tree item with text:

    ```python
    rio.SimpleTreeItem("Root Node", key="root")
    ```

    A more complex example with secondary text, children, and event handling:

    ```python
    import functools

    class MyComponent(rio.Component):
        def on_press(self, item: str) -> None:
            print(f"Pressed {item}")

        def build(self) -> rio.Component:
            return rio.TreeView(
                rio.SimpleTreeItem(
                    text="Parent",
                    secondary_text="Details\\nMore details",
                    key="parent",
                    left_child=rio.Icon("material/folder"),
                    right_child=rio.Button("Action"),
                    children=[rio.SimpleTreeItem("Child", key="child")],
                    is_expanded=True,
                    on_press=functools.partial(self.on_press, "Parent"),
                ),
                selection_mode="multiple",
            )
    ```
    """

    secondary_text: str = ""
    left_child: Component | None = None
    right_child: Component | None = None

    def __init__(
        self,
        text: str,
        *,
        key: str | int | None = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        secondary_text: str = "",
        left_child: Component | None = None,
        right_child: Component | None = None,
        children: list[te.Self] | None = None,
        is_expanded: bool = False,
        on_press: EventHandler[[]] = None,
        on_expansion_changed: EventHandler[bool] = None,
    ) -> None:
        super().__init__(
            text,
            key=key,
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
            children=children,
            is_expanded=is_expanded,
            on_press=on_press,
            on_expansion_changed=on_expansion_changed,
        )
        self.secondary_text = secondary_text
        self.left_child = left_child
        self.right_child = right_child

    def build_content(self) -> Component:
        children = []
        if self.left_child:
            children.append(self.left_child)
        text_children = [super().build_content()]
        if self.secondary_text:
            text_children.append(
                Text(
                    self.secondary_text,
                    overflow="wrap",
                    style="dim",
                    justify="left",
                    selectable=False,
                )
            )
        children.append(
            Column(
                *text_children,
                spacing=0.5,
                grow_x=True,
                align_y=0.5,
                grow_y=False,
            )
        )
        if self.right_child:
            children.append(self.right_child)
        return Row(*children, spacing=1, grow_x=True)
