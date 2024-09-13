from __future__ import annotations

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "AspectRatioContainer",
]


class AspectRatioContainer(FundamentalComponent):
    """
    Contains a single child, maintaining a fixed aspect ratio.

    `AspectRatioContainer` is a container which contains just a single child.
    What makes it special, is that it always maintains a fixed aspect ratio,
    i.e. width to height ratio. This is useful if you've got a component that
    you want to be able to resize, without distorting it.


    ## Attributes

    `content`: The component to place inside the container.

    `aspect_ratio`: The aspect ratio to maintain. This is the desired width
        divided by the desired height.


    ## Examples

    This will create a Rectangle that scales up to fit the parent container, but
    always maintains a 16:9 aspect ratio:

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.AspectRatioContainer(
                content=rio.Rectangle(
                    content=rio.Text(
                        "Hello World!",
                        justify="center",
                    ),
                    fill=rio.Color.RED,
                ),
                aspect_ratio=16 / 9,
            )
    ```


    ## Metadata

    `public`: False

    `experimental`: True
    """

    content: rio.Component
    aspect_ratio: float


AspectRatioContainer._unique_id_ = "AspectRatioContainer-builtin"
