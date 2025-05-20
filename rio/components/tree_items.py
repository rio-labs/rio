from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings
from uniserde import JsonDoc

import rio

from ..utils import EventHandler
from .component import AccessibilityRole, Component, Key
from .fundamental_component import FundamentalComponent

__all__ = [
    "CustomTreeItem",
    "SimpleTreeItem",
]


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class TreeItemExpansionChangeEvent:
    """
    Holds information regarding the change of a tree item's `is_expanded` state.

    This is a simple dataclass that stores useful information for when the user
    opens or closes a tree item. You'll typically receive this as argument in
    `on_expansion_change` events.

    ## Attributes

    `is_expanded`: The new `is_expanded` state of the tree item.
    """

    is_expanded: bool


class _TreeItemBase(Component):
    """
    ## Attributes

    `children`: A list of nested tree items.

    `is_expanded`: Whether the children are visible.

    `on_press`: Triggered when the item is pressed.

    `on_expansion_change`: Triggered when the expansion state changes.

    `expand_button_open`: Component to display when the item is expanded and has
        children.

    `expand_button_closed`: Component to display when the item is collapsed and
        has children.

    `expand_button_disabled`: Component to display when the item has no
        children.
    """

    expand_button_open: Component
    expand_button_closed: Component
    expand_button_disabled: Component
    children: list[SimpleTreeItem | CustomTreeItem] = []
    is_expanded: bool = False
    on_press: EventHandler[[]] = None
    on_expansion_change: EventHandler[TreeItemExpansionChangeEvent] = None

    def __init__(
        self,
        *,
        is_expanded: bool = False,
        on_press: EventHandler[[]] = None,
        on_expansion_change: EventHandler[TreeItemExpansionChangeEvent] = None,
        children: list[SimpleTreeItem | CustomTreeItem] | None = None,
        expand_button_open: Component | None = None,
        expand_button_closed: Component | None = None,
        expand_button_disabled: Component | None = None,
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

        if expand_button_open is None:
            expand_button_open = make_default_expand_button(
                "material/arrow_drop_down"
            )

        if expand_button_closed is None:
            expand_button_closed = make_default_expand_button(
                "material/arrow_right"
            )

        if expand_button_disabled is None:
            expand_button_disabled = make_default_expand_button(
                "material/circle"
            )

        self.is_expanded = is_expanded
        self.on_press = on_press
        self.on_expansion_change = on_expansion_change
        self.children = [] if children is None else children
        self.expand_button_open = expand_button_open
        self.expand_button_closed = expand_button_closed
        self.expand_button_disabled = expand_button_disabled


def make_default_expand_button(icon_name: str) -> Component:
    return rio.Icon(
        icon_name,
        min_width=1,
        min_height=1,
        align_x=0.5,
        align_y=0.5,
    )


@t.final
class CustomTreeItem(_TreeItemBase, FundamentalComponent):
    """
    A tree item with customizable content.

    `CustomTreeItem` is the core building block for tree structures in Rio. It
    displays a content area and relies on the frontend to render an expand
    button and children container based on serialized data. The expand button's
    appearance can be customized with components for open, closed, and disabled
    states.

    ## Attributes

    `content`: The primary content to display in the tree item.

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

    ## Metadata

    `experimental`: True
    """

    content: Component | None = None

    def __init__(
        self,
        content: Component,
        *,
        is_expanded: bool = False,
        on_press: EventHandler[[]] = None,
        on_expansion_change: EventHandler[TreeItemExpansionChangeEvent] = None,
        children: list[SimpleTreeItem | CustomTreeItem] | None = None,
        expand_button_open: Component | None = None,
        expand_button_closed: Component | None = None,
        expand_button_disabled: Component | None = None,
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
            children=children,
            is_expanded=is_expanded,
            on_press=on_press,
            on_expansion_change=on_expansion_change,
            expand_button_open=expand_button_open,
            expand_button_closed=expand_button_closed,
            expand_button_disabled=expand_button_disabled,
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

        self.content = content

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

            if self.on_expansion_change:
                # Trigger the expansion change
                await self.call_event_handler(
                    self.on_expansion_change,
                    TreeItemExpansionChangeEvent(is_expanded),
                )

            self._apply_delta_state_from_frontend({"is_expanded": is_expanded})
        else:
            assert False, f"Unexpected message type: {msg.get('type')}"

        # Refresh the session
        await self.session._refresh()


CustomTreeItem._unique_id_ = "CustomTreeItem-builtin"


class SimpleTreeItem(_TreeItemBase):
    """
    A simple tree item with a header, optional secondary text, and children.

    `SimpleTreeItem` provides a convenient way to create tree items with primary
    text, optional secondary text, and left/right children (e.g., icons or
    buttons). The expand button can be customized via open, closed, and disabled
    components passed to the frontend.

    ## Attributes

    `text`: The primary text or component to display.

    `secondary_text`: Additional text to display below the primary text.

    `left_child`: A component to display on the left side of the item.

    `right_child`: A component to display on the right side of the item.

    ## Examples

    A minimal tree item:

    ```python
    rio.SimpleTreeItem(
        text="Root Node",
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

    ## Metadata

    `experimental`: True
    """

    content: str | Component = ""
    secondary_text: str = ""
    left_child: Component | None = None
    right_child: Component | None = None

    def __init__(
        self,
        content: str | Component,
        *,
        secondary_text: str = "",
        left_child: Component | None = None,
        right_child: Component | None = None,
        children: list[SimpleTreeItem | CustomTreeItem] | None = None,
        is_expanded: bool = False,
        on_expansion_change: EventHandler[TreeItemExpansionChangeEvent] = None,
        on_press: EventHandler[[]] = None,
        expand_button_open: Component | None = None,
        expand_button_closed: Component | None = None,
        expand_button_disabled: Component | None = None,
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
            children=children,
            is_expanded=is_expanded,
            on_press=on_press,
            on_expansion_change=on_expansion_change,
            expand_button_open=expand_button_open,
            expand_button_closed=expand_button_closed,
            expand_button_disabled=expand_button_disabled,
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

        self.content = content
        self.secondary_text = secondary_text
        self.left_child = left_child
        self.right_child = right_child

    def build(self) -> Component:
        children: list[Component] = []
        content_children: list[Component] = []

        if self.left_child:
            children.append(self.left_child)

        if isinstance(self.content, Component):
            content_children.append(self.content)
        else:
            content_children.append(
                rio.Text(self.content, justify="left", selectable=False)
            )

        if self.secondary_text:
            content_children.append(
                rio.Text(
                    self.secondary_text,
                    overflow="wrap",
                    style="dim",
                    justify="left",
                    selectable=False,
                )
            )

        children.append(
            rio.Column(
                *content_children,
                spacing=0.5,
                grow_x=True,
                align_y=0.5,
                grow_y=False,
            )
        )

        if self.right_child:
            children.append(self.right_child)

        return CustomTreeItem(
            content=rio.Row(*children, spacing=1, grow_x=True),
            is_expanded=self.bind().is_expanded,
            on_press=self.on_press,
            on_expansion_change=self.on_expansion_change,
            children=self.children,
            expand_button_open=self.expand_button_open,
            expand_button_closed=self.expand_button_closed,
            expand_button_disabled=self.expand_button_disabled,
            key=self.key,
        )
