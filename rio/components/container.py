from __future__ import annotations

import typing as t

import rio

from .component import Component

__all__ = [
    "Container",
]


@t.final
class Container(Component):
    """
    An invisible component holding a single child.

    `Container` is a simple container which holds a single child component. It
    is useful when you receive a component as attribute and wish to add
    additional layout attributes such as a margin.


    ## Attributes

    `content`: The component to place inside the container.


    ## Examples

    This minimal example will simply display a `container` with the text "Hello
    World!" and a margin of 2:

    ```python
    rio.Container(
        rio.Text("Hello World!"),
        margin=2,
    )
    ```

    `Container`s are commonly used to add layout attributes to a single child.
    You can easily achieve this by adding the content to the container and then
    adding the layout attributes:

    ```python
    class MyComponent(rio.Component):
        content: rio.Component

        def build(self) -> rio.Component:
            # We'd like to center `self.content`, but can't do that via the
            # constructor because it was already instantiated by our parent.
            # An easy way around this is to wrap it in a `rio.Container`:
            return rio.Container(
                self.content,
                align_x=0.5,
            )
    """

    content: rio.Component

    def build(self) -> rio.Component:
        return self.content
