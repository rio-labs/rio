import typing as t
from abc import ABC, abstractmethod

import typing_extensions as te
from uniserde import JsonDoc

from ..observables import Dataclass
from ..utils import EventHandler
from .component import AccessibilityRole, Component, Key
from .fundamental_component import FundamentalComponent
from .linear_containers import Column, Row
from .text import Text

__all__ = ["CustomTreeItem", "AbstractTreeItem", "SimpleTreeItem"]


@t.final
class CustomTreeItem(FundamentalComponent):
    """
    A fundamental tree item component with customizable content.

    `CustomTreeItem` is the core building block for tree structures in Rio. It displays a content
    area and relies on the frontend to render an expand button and children container based on
    serialized data. The expand button's appearance can be customized with components for open,
    closed, and disabled states.

    ## Attributes

    `content`: The primary content to display in the tree item.

    `is_expanded`: Whether the children are currently visible. Defaults to False.

    `on_expansion_change`: Event handler triggered when the expansion state changes.

    `expand_button_open`: Component to display when the item is expanded and has children.

    `expand_button_closed`: Component to display when the item is collapsed and has children.

    `expand_button_disabled`: Component to display when the item has no children.

    ## Examples

    A minimal tree item:

    ```python
    rio.CustomTreeItem(
        content=rio.Text("Leaf Node"),
        key="leaf",
    )
    ```

    A tree item with custom expand button icons:

    ```python
    rio.CustomTreeItem(
        content=rio.Text("Parent Node"),
        expand_button_open=rio.Icon("material/arrow_drop_down"),
        expand_button_closed=rio.Icon("material/arrow_right"),
        expand_button_disabled=rio.Icon("material/circle"),
        is_expanded=False,
        on_expansion_change=lambda expanded: print(f"Expanded: {expanded}"),
        key="parent",
        children=[
            rio.CustomTreeItem(content=rio.Text("Child Node"), key="child"),
        ],
    )
    ```
    """

    content: Component
    is_expanded: bool = False
    on_press: EventHandler[[]] = None
    on_expansion_change: EventHandler[bool] = None
    children: list[Component] = []
    expand_button_open: Component | None = None
    expand_button_closed: Component | None = None
    expand_button_disabled: Component | None = None

    def __init__(
        self,
        content: Component,
        *,
        key: str | int | None = None,
        on_press: EventHandler[[]] = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        is_expanded: bool = False,
        on_expansion_change: EventHandler[bool] = None,
        children: list[Component] = [],
        expand_button_open: Component | None = None,
        expand_button_closed: Component | None = None,
        expand_button_disabled: Component | None = None,
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
        self.is_expanded = is_expanded
        self.on_press = on_press
        self.on_expansion_change = on_expansion_change
        self.children = children
        self.expand_button_open = expand_button_open
        self.expand_button_closed = expand_button_closed
        self.expand_button_disabled = expand_button_disabled

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "pressable": self.on_press is not None,
        }

    async def _on_message_(self, msg: t.Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), f"Unexpected message: {msg}"

        msg_type: str = msg["type"]
        assert isinstance(msg_type, str), msg_type

        if msg_type == "press":
            # Trigger the press event
            if self.on_press is not None:
                await self.call_event_handler(self.on_press)
        elif msg_type == "toggleExpansion":
            is_expanded = msg.get("is_expanded")
            assert isinstance(is_expanded, bool), (
                f"Invalid is_expanded: {is_expanded}"
            )
            self._apply_delta_state_from_frontend({"is_expanded": is_expanded})

            if self.on_expansion_change:
                # Trigger the expansion change
                await self.call_event_handler(
                    self.on_expansion_change, is_expanded
                )
        else:
            assert False, f"Unexpected message type: {msg.get('type')}"

        # Refresh the session
        await self.session._refresh()


CustomTreeItem._unique_id_ = "CustomTreeItem-builtin"


class AbstractTreeItem(ABC, Dataclass):
    """
    A minimal mixin for tree items with expandable children and event handling.

    `AbstractTreeItem` defines the essential attributes for tree items, including children,
    expansion state, and custom expand button components. It is not a `Component` and must be
    mixed with a `Component` subclass that implements the `build` method. The
    `custom_tree_item` method wraps content in a `CustomTreeItem`, relying on the frontend to
    render the expand button and children container.

    ## Attributes

    `children`: A list of nested tree items. Defaults to an empty list.

    `is_expanded`: Whether the children are visible. Defaults to False.

    `on_press`: Triggered when the item is pressed.

    `on_expansion_change`: Triggered when the expansion state changes.

    `expand_button_open`: Component to display when the item is expanded and has children.

    `expand_button_closed`: Component to display when the item is collapsed and has children.

    `expand_button_disabled`: Component to display when the item has no children.

    ## Examples

    A custom tree item with `AbstractTreeItem`:

    ```python
    class TextTreeItem(rio.Text, rio.AbstractTreeItem):
        def build(self) -> rio.Component:
            return self.custom_tree_item(super().build())

    rio.TextTreeItem(
        text="Leaf Node",
        expand_button_disabled=rio.Icon("material/circle"),
        key="leaf",
    )
    ```
    """

    children: list[te.Self] = []
    is_expanded: bool = False
    on_press: EventHandler[[]] = None
    on_expansion_change: EventHandler[bool] = None
    expand_button_open: Component | None = None
    expand_button_closed: Component | None = None
    expand_button_disabled: Component | None = None

    def custom_tree_item(self, content: Component) -> Component:
        return CustomTreeItem(
            content=content,
            is_expanded=self.bind().is_expanded,
            on_press=self.on_press,
            on_expansion_change=self.on_expansion_change,
            children=self.children,
            expand_button_open=self.expand_button_open
            or Text("▼", selectable=False),
            expand_button_closed=self.expand_button_closed
            or Text("▶", selectable=False),
            expand_button_disabled=self.expand_button_disabled
            or Text("●", selectable=False),
            key="",
        )

    @abstractmethod
    def build(self) -> Component: ...


class SimpleTreeItem(Component, AbstractTreeItem):
    """
    A simple tree item with a header, optional secondary text, and children.

    `SimpleTreeItem` combines `AbstractTreeItem` with a `Component` to provide a convenient
    way to create tree items with primary text, optional secondary text, and left/right
    children (e.g., icons or buttons). The expand button can be customized via open, closed,
    and disabled components passed to the frontend.

    ## Attributes

    `text`: The primary text to display.

    `secondary_text`: Additional text to display below the primary text.

    `left_child`: A component to display on the left side of the item.

    `right_child`: A component to display on the right side of the item.

    `children`: A list of nested tree items. Defaults to an empty list.

    `is_expanded`: Whether the children are visible. Defaults to False.

    `on_press`: Triggered when the item is pressed.

    `on_expansion_change`: Triggered when the expansion state changes.

    `expand_button_open`: Component for the expand button when expanded.

    `expand_button_closed`: Component for the expand button when collapsed.

    `expand_button_disabled`: Component for the expand button when no children exist.

    ## Examples

    A minimal tree item:

    ```python
    rio.SimpleTreeItem(
        text="Root Node",
        expand_button_disabled=rio.Icon("material/circle"),
        key="root",
    )
    ```

    A complex tree item with custom button icons and event handling:

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
                    left_child=rio.Icon("material/star"),
                    right_child=rio.Button("Action"),
                    expand_button_open=rio.Icon("material/arrow_drop_down"),
                    expand_button_closed=rio.Icon("material/arrow_right"),
                    expand_button_disabled=rio.Icon("material/circle"),
                    children=[rio.SimpleTreeItem(text="Child", key="child")],
                    is_expanded=True,
                    on_press=functools.partial(self.on_press, "Parent"),
                ),
                selection_mode="multiple",
            )
    ```
    """

    text: str = ""
    secondary_text: str = ""
    left_child: Component | None = None
    right_child: Component | None = None

    def __init__(
        self,
        text: str,
        *,
        children: list[AbstractTreeItem] = [],
        is_expanded: bool = False,
        on_expansion_change: EventHandler[bool] = None,
        key: Key | None = None,
        secondary_text: str = "",
        left_child: Component | None = None,
        right_child: Component | None = None,
        on_press: EventHandler[[]] = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
        expand_button_open: Component | None = None,
        expand_button_closed: Component | None = None,
        expand_button_disabled: Component | None = None,
    ) -> None:
        Component.__init__(
            self,
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
            key=key,
            accessibility_role=accessibility_role,
        )
        AbstractTreeItem.__init__(
            self,
            children=children,
            is_expanded=is_expanded,
            on_press=on_press,
            on_expansion_change=on_expansion_change,
            expand_button_open=expand_button_open,
            expand_button_closed=expand_button_closed,
            expand_button_disabled=expand_button_disabled,
        )
        self.text = text
        self.secondary_text = secondary_text
        self.left_child = left_child
        self.right_child = right_child

    def build(self) -> Component:
        children = []
        if self.left_child:
            children.append(self.left_child)
        content_children = []
        if isinstance(self.text, Component):
            content_children.append(self.text)
        else:
            content_children.append(
                Text(self.text, justify="left", selectable=False)
            )
        if self.secondary_text:
            content_children.append(
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
                *content_children,
                spacing=0.5,
                grow_x=True,
                align_y=0.5,
                grow_y=False,
            )
        )
        if self.right_child:
            children.append(self.right_child)
        return self.custom_tree_item(Row(*children, spacing=1, grow_x=True))
