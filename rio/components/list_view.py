from __future__ import annotations

from typing import Literal, final

from typing_extensions import Self

import rio

from .fundamental_component import FundamentalComponent

__all__ = ["ListView"]


@final
class ListView(FundamentalComponent):
    """
    Vertically arranges and styles its children.

    A container which arranges its children in a vertical list. It is similar to
    `Column`, but it is optimized for displaying large numbers of items.


    ## Attributes

    `children`: The children to display in the list.

    `key`: A unique key for this component. If the key changes, the component
        will be destroyed and recreated. This is useful for components which
        maintain state across rebuilds.


    ## Examples

    A minimal example of a `ListView` with two items will be shown:

    ```python
    rio.ListView(
        rio.SimpleListItem("Product 1", key="item1"),
        rio.SimpleListItem("Product 2", key="item2"),
    )
    ```

    `ListView`s are commonly used to display lists of dynamic length. You can easily
    achieve this by adding the children to a list first, and then unpacking that list:

    ```python
    import functools


    class MyComponent(rio.Component):
        products: list[str] = ["Product 1", "Product 2", "Product 3"]

        def on_press_heading_list_item(self, product: str) -> None:
            print(f"Selected {product}")

        def build(self) -> rio.Component:
            # Store all children in an intermediate list
            list_items = []

            for product in self.products:
                list_items.append(
                    rio.SimpleListItem(
                        text=product,
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

    children: list[rio.Component]

    def __init__(
        self,
        *children: rio.Component,
        key: str | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        width: float | Literal["natural", "grow"] = "natural",
        height: float | Literal["natural", "grow"] = "natural",
        align_x: float | None = None,
        align_y: float | None = None,
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
            width=width,
            height=height,
            align_x=align_x,
            align_y=align_y,
        )

        self.children = list(children)

    def add(self, child: rio.Component) -> Self:
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


ListView._unique_id = "ListView-builtin"
