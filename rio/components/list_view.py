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

    Lists of items are a common pattern in user interfaces. Whether you need to
    display a list of products, messages, or any other kind of data, the
    `ListView` component is here to help.

    List views are similar to columns, in that they arrange their children
    vertically. However, they also apply a default style to their content which
    allows you to group items together in a visually distinct way.

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

    `key`: A unique key for this component. If the key changes, the component
        will be destroyed and recreated. This is useful for components which
        maintain state across rebuilds.


    ## Examples

    This example will display a list of two products:

    ```python
    rio.ListView(
        rio.SimpleListItem("Product 1", key="item1"),
        rio.SimpleListItem("Product 2", key="item2"),
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
            print(f"Selected {product}")

        def build(self) -> rio.Component:
            # First create the ListView
            result = rio.ListView()

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
