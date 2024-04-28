from __future__ import annotations

from typing import *  # type: ignore

import rio

from .component import Component

__all__ = [
    "Container",
]


@final
class Container(Component):
    """
    A component holding a single child.

    `Container` is a simple container which holds a single child component. It
    is useful for when you receive a component as child and wish to add
    additional layout attributes such as a margin.


    ## Attributes

    `content`: The component to place inside the container.


    ## Examples

    This minimal example will simply display a `container` with the text "Hello
    World!":

    ```python
    rio.Container(rio.Text("Hello World!"))
    ```

    `Container`s are commonly used to add layout attributes to a single child.
    You can easily achieve this by adding the content to the container and then
    adding the layout attributes:

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Container(
                rio.Text("Hello World!"),
                margin=2,
            )
    """

    content: rio.Component

    def build(self) -> rio.Component:
        return self.content
