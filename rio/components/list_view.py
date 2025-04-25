from __future__ import annotations

import dataclasses
import typing as t

import typing_extensions as te
from uniserde import JsonDoc

import rio

from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = ["ListView", "ListViewSelectionChangeEvent"]


@t.final
@dataclasses.dataclass
class ListViewSelectionChangeEvent:
    """
    Event triggered when the selection in a `ListView` changes.

    ## Attributes:
        `selected_items`: A list of keys of the currently selected items.
    """

    selected_items: list[Key]


@t.final
class ListView(FundamentalComponent):
    """
    Vertically arranges and styles its children with optional selection support.

    Lists of items are a common pattern in user interfaces. Whether you need to
    display a list of products, messages, or any other kind of data, the
    `ListView` component is here to help.

    List views are similar to columns, in that they arrange their children
    vertically. However, they also apply a default style to their content which
    allows you to group items together in a visually distinct way. Additionally,
    `ListView` supports single or multiple item selection.

    Rio ships with several components which are meant specifically to be used
    inside of `ListView`s:

    - `SimpleListItem`: A typical list item which can display text, subtext and
      icons.
    - `CustomListItem`: A list item which can display any component as its
      content, while still applying the typical list item theming and layout.
    - `HeadingListItem`: For labelling groups of similar items.
    - `SeparatorListItem`: Leaves a gap between items, so you can group them
      visually.

    ## Attributes

    `children`: The children to display in the list.

    `selection_mode`: Determines the selection behavior: "none" (no selection),
        "single" (one item selectable), or "multiple" (multiple items selectable).
        Defaults to "none".

    `selected_items`: A list of keys of currently selected items. Defaults to
        an empty list.

    `on_selection_change`: Event handler triggered when the selection changes.

    `key`: A unique key for this component. If the key changes, the component
        will be destroyed and recreated. This is useful for components which
        maintain state across rebuilds.

    ## Examples

    This example will display a list of two products with single selection:

    ```python
    rio.ListView(
        rio.SimpleListItem("Item 1", key="item1"),
        rio.SimpleListItem("Item 2", key="item2"),
        selection_mode="single",
        selected_items=["item1"],  # Preselect the first item
    )
    ```

    `ListView`s are commonly used to display lists of dynamic length. You can
    easily achieve this by first creating a `ListView`, then adding the children
    after the fact:

    ```python
    import functools


    class MyComponent(rio.Component):
        products: list[str] = ["Product 1", "Product 2", "Product 3"]

        def on_press_heading_list_item(self, product: str) -> None:
            print(f"Pressed {product}")

        def on_selection_change(self, selected_items) -> None:
            print(f"Selected keys: {selected_items}")

        def build(self) -> rio.Component:
            # First create the ListView
            result = rio.ListView(
                *[rio.SimpleListItem(text=p, key=p) for p in self.products],
                selection_mode="multiple",
                on_selection_change=self.on_selection_change,
            )

            # Then add the children one by one
            for product in self.products:
                result.add(
                    rio.SimpleListItem(
                        text=product,
                        key=product,
                        # Note the use of `functools.partial` to pass the
                        # product to the event handler.
                        on_press=functools.partial(
                            self.on_press_heading_list_item,
                            product=product,
                        ),
                    )
                )

            return result
    ```
    """

    children: list[rio.Component]
    selection_mode: t.Literal["none", "single", "multiple"]
    selected_items: list[Key]
    on_selection_change: rio.EventHandler[ListViewSelectionChangeEvent]

    def __init__(
        self,
        *children: rio.Component,
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
        selection_mode: t.Literal["none", "single", "multiple"] = "none",
        selected_items: list[Key] | None = None,
        on_selection_change: rio.EventHandler[
            ListViewSelectionChangeEvent
        ] = None,
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

        self.children = list(children)
        self.selection_mode = selection_mode
        self.selected_items = selected_items or []
        self.on_selection_change = on_selection_change

    def add(self, child: rio.Component) -> te.Self:
        """
        Appends a child component.

        Appends a child component to the end and then returns the `ListView`,
        which makes method chaining possible:

        ```python
        rio.ListView().add(child1).add(child2)
        ```

        ## Parameters

        `child`: The child component to append.
        """
        self.children.append(child)
        return self

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "selected_items": self.selected_items,  # type: ignore (variance)
        }

    async def _on_message_(self, msg: t.Any) -> None:
        """
        Handle messages from the frontend, such as selection changes.
        """
        # Validate the message
        assert isinstance(msg, dict), msg
        assert msg["type"] == "selectionChange", msg

        msg_type: str = msg["type"]
        assert isinstance(msg_type, str), msg_type

        selected_items: list[str | int] = msg["selected_items"]
        selection_mode: str = self.selection_mode
        if selection_mode == "single":
            assert len(selected_items) < 2, (
                "Only zero or one keys may be selected in single selection mode"
            )
        else:
            assert selection_mode == "multiple", (
                f"Unexpected selection change in {selection_mode} selection mode"
            )

        # Trigger the event
        await self.call_event_handler(
            self.on_selection_change,
            ListViewSelectionChangeEvent(selected_items),
        )

        # Update the state
        self._apply_delta_state_from_frontend(
            {"selected_items": selected_items}
        )


ListView._unique_id_ = "ListView-builtin"
