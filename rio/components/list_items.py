from __future__ import annotations

from typing import *  # type: ignore

from uniserde import JsonDoc

import rio

from .component import Component
from .fundamental_component import FundamentalComponent

__all__ = [
    "HeadingListItem",
    "SeparatorListItem",
    "SimpleListItem",
    "CustomListItem",
]


@final
class HeadingListItem(FundamentalComponent):
    """
    A simple list item with only a header.

    `HeadingListItem`s are the easiest way to create list items, which can take
    care of the most primitive task: Display a text. If your want a more generic
    list item with additional children, you can use the `SimpleListItem`. Or if
    you want to build a more complex list item, you can use the
    `CustomListItem`.

    ## Attributes

    `text`: The text to display


    ## Examples

    This minimal example will simply display a list item with the text "Click
    me!":

    ```python
    rio.HeadingListItem("Click me!", key="item1")
    ```

    `ListView`s are commonly used to display lists of dynamic length. You can
    easily achieve this by adding the children to a list first, and then
    unpacking that list:

    ```python
    class MyComponent(rio.Component):
        products: list[str] = ["Product 1", "Product 2", "Product 3"]

        def build(self) -> rio.Component:
            # Store all children in an intermediate list
            list_items = []

            for product in self.products:
                list_items.append(
                    rio.HeadingListItem(
                        text=product,
                        key=product,
                    )
                )

            # Then unpack the list to pass the children to the `ListView`
            return rio.ListView(*list_items)
    ```
    """

    text: str


HeadingListItem._unique_id = "HeadingListItem-builtin"


@final
class SeparatorListItem(FundamentalComponent):
    """
    A visual separator between list items.

    `SeparatorListItem`s allow you to group list items visually. They create
    create some empty vertical space between other list items. Normally,
    multiple consecutive list items are also visually grouped, by assigning them
    a card-like background. The `SeparatorListItem` breaks this grouping for
    additional visual separation.
    """


SeparatorListItem._unique_id = "SeparatorListItem-builtin"


@final
class SimpleListItem(Component):
    """
    A simple list item with a header and optional secondary text and children.

    `SimpleListItem`s are a convenient way to create list items, which can
    take care of the most common tasks: Display a text, optional secondary text
    and even additional children (e.g. icons or buttons) to the left and right.
    Most children are optional so you can only add whichever parts you need.


    ## Attributes

    `text`: The text to display.

    `secondary_text`: Additional text to display below the primary text. This
        text may span multiple lines (use `"\\n"` to add a line break).

    `left_child`: A component to display on the left side of the list item.

    `right_child`: A component to display on the right side of the list item.

    `on_press`: Triggered when the list item is pressed.


    ## Examples

    This minimal example will simply display a list item with the text "Click
    me!":

    ```python
    rio.SimpleListItem("Click me!", key="item1")
    ```

    `ListView`s are commonly used to display lists of dynamic length. You can
    easily achieve this by adding the children to a list first, and then
    unpacking that list:

    ```python
    import functools


    class MyComponent(rio.Component):
        products: list[str] = ["Product 1", "Product 2", "Product 3"]

        def on_press_simple_list_item(self, product: str) -> None:
            print(f"Selected {product}")

        def build(self) -> rio.Component:
            # Store all children in an intermediate list
            list_items = []

            for product in self.products:
                list_items.append(
                    rio.SimpleListItem(
                        text=product,
                        key=product,
                        left_child=rio.Icon("material/castle"),
                        # Note the use of `functools.partial` to pass the
                        # product to the event handler.
                        on_press=functools.partial(
                            self.on_press_simple_list_item,
                            product=product,
                        ),
                    )
                )

            # Then unpack the list to pass the children to the `ListView`
            return rio.ListView(*list_items)
    ```
    """

    text: str
    secondary_text: str
    left_child: rio.Component | None
    right_child: rio.Component | None
    on_press: rio.EventHandler[[]]

    def __init__(
        self,
        text: str,
        *,
        key: str | None = None,
        secondary_text: str = "",
        left_child: rio.Component | None = None,
        right_child: rio.Component | None = None,
        on_press: rio.EventHandler[[]] = None,
        width: float | Literal["natural", "grow"] = "natural",
        height: float | Literal["natural", "grow"] = "natural",
    ) -> None:
        super().__init__(
            width=width,
            height=height,
            key=key,
        )

        self.text = text
        self.secondary_text = secondary_text
        self.left_child = left_child
        self.right_child = right_child
        self.on_press = on_press

    def build(self) -> rio.Component:
        children = []

        # Left child
        if self.left_child is not None:
            children.append(self.left_child)

        # Main content (text)
        text_children = [
            rio.Text(
                self.text,
                justify="left",
            )
        ]

        if self.secondary_text:
            text_children.append(
                rio.Text(
                    self.secondary_text,
                    wrap=True,
                    style="dim",
                    justify="left",
                )
            )

        children.append(
            rio.Column(
                *text_children,
                spacing=0.5,
                width="grow",
                align_y=0.5,  # In case too much space is allocated
            )
        )

        # Right child
        if self.right_child is not None:
            children.append(self.right_child)

        # Combine everything
        return CustomListItem(
            content=rio.Row(
                *children,
                spacing=1,
                width="grow",
            ),
            on_press=self.on_press,
            key="",
        )


@final
class CustomListItem(FundamentalComponent):
    """
    A list item with custom content.

    Most of the time the `SimpleListItem` will do the job. With
    `CustomListItems` you can build more complex list items. You can add any
    component to the list item. This can be e.g. a `Row`, `Column`, `Text`,
    `Icon`, `Image` or any other component.


    ## Attributes

    `content`: The content to display.

    `on_press`: Triggered when the list item is pressed.

    `key`: A unique key to identify the list item. This is used to avoid
        unintentional reconciliation with other items when the list is
        updated.


    ## Examples

    Instead of using the `SimpleListItem` you can use the `CustomListItem` to create
    a custom list item. This can be useful if you want to add more complex content
    to the list item. You can add any component to the list item.

    ```python
    class MyCustomListItemComponent(rio.Component):
        # create a custom list item
        product: str
        button_text: str

        def build(self) -> rio.Component:

            return rio.Row(
                rio.Text(self.product),
                rio.Spacer(),
                rio.Button(
                    self.button_text,
                    on_press=lambda: print("Hello, world!"),
                ),
            )


    class MyComponent(rio.Component):
        products: list[str] = ["Product 1", "Product 2", "Product 3"]

        def on_press_heading_list_item(self, product: str) -> None:
            print(f"Selected {product}")

        def build(self) -> rio.Component:
            # Store all children in an intermediate list
            list_items = []

            for product in self.products:
                list_items.append(
                    rio.CustomListItem(
                        # Use the `MyCustomListItem` component to create a custom list item
                        content=MyCustomListItemComponent(
                            product=product, button_text="Click Me!"
                        ),
                        key=product,
                        # Note the use of `functools.partial` to pass the product
                        # to the event handler.
                        on_press=functools.partial(
                            self.on_press_heading_list_item,
                            product=product,
                        ),
                    )
                )

            # Then unpack the list to pass the children to the `ListView`
            return rio.ListView(*list_items)
    ```
    """

    content: rio.Component
    on_press: rio.EventHandler[[]]

    def __init__(
        self,
        content: rio.Component,
        *,
        key: str | None = None,
        on_press: rio.EventHandler[[]] = None,
        width: float | Literal["natural", "grow"] = "natural",
        height: float | Literal["natural", "grow"] = "natural",
    ) -> None:
        super().__init__(
            width=width,
            height=height,
            key=key,
        )

        self.content = content
        self.on_press = on_press

    def _custom_serialize(self) -> JsonDoc:
        return {
            "pressable": self.on_press is not None,
        }

    async def _on_message(self, msg: Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg
        assert msg["type"] == "press", msg

        msg_type: str = msg["type"]
        assert isinstance(msg_type, str), msg_type

        if self.on_press is None:
            return

        # Trigger the press event
        await self.call_event_handler(self.on_press)

        # Refresh the session
        await self.session._refresh()


CustomListItem._unique_id = "CustomListItem-builtin"
