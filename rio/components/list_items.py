from __future__ import annotations

import typing as t

from uniserde import JsonDoc

import rio

from .component import AccessibilityRole, Component, Key
from .fundamental_component import FundamentalComponent

__all__ = [
    "HeadingListItem",
    "SeparatorListItem",
    "SimpleListItem",
    "CustomListItem",
]


@t.final
class HeadingListItem(FundamentalComponent):
    """
    A list item acting as heading.

    `HeadingListItem`s are an easy way to add structure to your lists. They
    display a short text and style it as heading.

    If your want a more generic list item with additional children, consider
    `SimpleListItem` instead. If that's not enough for your needs you can build
    arbitrarily complex ones using `CustomListItem`.

    ## Attributes

    `text`: The text to display


    ## Examples

    This minimal example will simply display a list item with the text "I am
    a header":

    ```python
    rio.HeadingListItem("I am a header", key="item1")
    ```

    `ListView`s are commonly used to display lists of dynamic length. You can
    easily achieve this by first creating an empty `ListView`, then adding the
    children after the fact:

    ```python
    class MyComponent(rio.Component):
        products: list[str] = ["Product 1", "Product 2", "Product 3"]

        def build(self) -> rio.Component:
            # Start off empty
            result = rio.ListView()

            # Add a heading
            result.add(
                rio.HeadingListItem(
                    text="Our Products",
                    key="heading",
                )
            )

            # Add all products as SimpleListItems
            for product in self.products:
                result.add(
                    rio.SimpleListItem(
                        text=product,
                        key=product,
                    )
                )

            # Done!
            return result
    ```
    """

    text: str


HeadingListItem._unique_id_ = "HeadingListItem-builtin"


@t.final
class SeparatorListItem(FundamentalComponent):
    """
    A visual separator between list items.

    `SeparatorListItem`s allow you to group list items visually. They create
    some empty vertical space between other list items. Normally, multiple
    consecutive list items are also visually grouped, by assigning them a
    card-like background. The `SeparatorListItem` breaks this grouping for
    additional visual separation.

    ## Examples

    This minimal example will simply display a separator list item:

    ```python
    rio.SeparatorListItem()
    ```

    `ListView`s are commonly used to display lists of dynamic length. You can
    easily achieve this by first creating an empty `ListView`, then adding the
    children after the fact:

    ```python
    class MyComponent(rio.Component):
        products: list[str] = ["Product 1", "Product 2", "Product 3"]

        def build(self) -> rio.Component:
            # Start off empty
            result = rio.ListView()

            # Add all products as SimpleListItems
            for product in self.products:
                result.add(
                    rio.SimpleListItem(
                        text=product,
                        key=product,
                    )
                )
                # Add a separator
                result.add(rio.SeparatorListItem())

            # Done!
            return result
    ```
    """


SeparatorListItem._unique_id_ = "SeparatorListItem-builtin"


@t.final
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
    easily achieve this by first creating an empty `ListView`, then adding the
    children after the fact:

    ```python
    import functools


    class MyComponent(rio.Component):
        products: list[str] = ["Product 1", "Product 2", "Product 3"]

        def on_press_simple_list_item(self, product: str) -> None:
            print(f"Selected {product}")

        def build(self) -> rio.Component:
            # Start off empty
            result = rio.ListView()

            # Add all items
            for product in self.products:
                result.add(
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

            # Done!
            return result
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
        key: Key | None = None,
        secondary_text: str = "",
        left_child: rio.Component | None = None,
        right_child: rio.Component | None = None,
        on_press: rio.EventHandler[[]] = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
    ) -> None:
        super().__init__(
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
                selectable=False,
            )
        ]

        if self.secondary_text:
            text_children.append(
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
                *text_children,
                spacing=0.5,
                grow_x=True,
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
                grow_x=True,
            ),
            on_press=self.on_press,
            key=self.key,
        )


@t.final
class CustomListItem(FundamentalComponent):
    """
    A list item with custom content.

    Most of the time the `SimpleListItem` will do the job. With
    `CustomListItem`s you can build more complex list items. You can add any
    component to the list item. This can be e.g. a `Row`, `Column`, `Text`,
    `Icon`, `Image` or any other component.


    ## Attributes

    `content`: The content to display.

    `on_press`: Triggered when the list item is pressed.


    ## Examples

    Instead of using the `SimpleListItem` you can use the `CustomListItem` to create
    a custom list item. This can be useful if you want to add more complex content
    to the list item. You can add any component to the list item.

    ```python
    import functools


    class MyCustomListItemComponent(rio.Component):
        # Create a custom list item
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
            # Start off empty
            result = rio.ListView()

            # Add all items
            for product in self.products:
                result.add(
                    rio.CustomListItem(
                        # Use the `MyCustomListItem` component to create a
                        # custom list item
                        content=MyCustomListItemComponent(
                            product=product, button_text="Click Me!"
                        ),
                        key=product,
                        # Note the use of `functools.partial` to pass the
                        # product to the event handler.
                        on_press=functools.partial(
                            self.on_press_heading_list_item,
                            product=product,
                        ),
                    )
                )

            # Done!
            return result
    ```
    """

    content: rio.Component
    on_press: rio.EventHandler[[]]

    def __init__(
        self,
        content: rio.Component,
        *,
        key: Key | None = None,
        on_press: rio.EventHandler[[]] = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
    ) -> None:
        super().__init__(
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

        self.content = content
        self.on_press = on_press

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "pressable": self.on_press is not None,
        }

    async def _on_message_(self, msg: t.Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg
        assert msg["type"] == "press", msg

        msg_type: str = msg["type"]
        assert isinstance(msg_type, str), msg_type

        if self.on_press is None:
            return

        # Trigger the press event
        await self.call_event_handler(self.on_press)


CustomListItem._unique_id_ = "CustomListItem-builtin"
