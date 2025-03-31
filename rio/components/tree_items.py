import typing as t

import typing_extensions as te

from ..utils import EventHandler
from .component import Component
from .fundamental_component import FundamentalComponent
from .linear_containers import Column, Row
from .text import Text

__all__ = ["CustomTreeItem", "AbstractTreeItem", "SimpleTreeItem"]


class CustomTreeItem(FundamentalComponent):
    content: Component
    expand_button: Component | None = None
    children_container: Component | None = None
    is_expanded: bool = False
    on_expansion_changed: EventHandler[bool] = None

    def __init__(
        self,
        content: Component,
        *,
        expand_button: Component | None = None,
        children_container: Component | None = None,
        is_expanded: bool = False,
        on_expansion_changed: EventHandler[bool] = None,
        key: str | int | None = None,
    ) -> None:
        super().__init__(key=key)
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

        # Update the state
        self._apply_delta_state_from_frontend({"is_expanded": is_expanded})

        if self.on_expansion_changed:
            await self.call_event_handler(
                self.on_expansion_changed, is_expanded
            )

        # Refresh the session
        await self.session._refresh()


CustomTreeItem._unique_id_ = "CustomTreeItem-builtin"


class AbstractTreeItem(Component):
    text: str
    children: list[te.Self] = []
    is_expanded: bool = False
    on_press: EventHandler[[]] = None
    on_expansion_changed: EventHandler[bool] = None

    def __init__(
        self,
        text: str,
        *,
        children: list[te.Self] | None = None,
        is_expanded: bool = False,
        on_press: EventHandler[[]] = None,
        on_expansion_changed: EventHandler[bool] = None,
        key: str | int | None = None,
    ) -> None:
        super().__init__(key=key)
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
                margin_left=2,  # Indentation
            )
        else:
            children_container = None

        return CustomTreeItem(
            expand_button=expand_button,
            content=self.build_content(),
            children_container=children_container,
            is_expanded=self.is_expanded,
            on_expansion_changed=self.on_expansion_changed,
        )


class SimpleTreeItem(AbstractTreeItem):
    secondary_text: str = ""
    left_child: Component | None = None
    right_child: Component | None = None

    def __init__(
        self,
        text: str,
        *,
        secondary_text: str = "",
        left_child: Component | None = None,
        right_child: Component | None = None,
        children: list[te.Self] | None = None,
        is_expanded: bool = False,
        on_press: EventHandler[[]] = None,
        on_expansion_changed: EventHandler[bool] = None,
        key: str | int | None = None,
    ) -> None:
        super().__init__(
            text,
            key=key,
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

        return Row(
            *children,
            spacing=1,
            grow_x=True,
        )
