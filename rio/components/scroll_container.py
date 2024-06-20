from __future__ import annotations

from dataclasses import KW_ONLY
from typing import Literal, final

import rio

from .. import deprecations
from .component import Component

__all__ = ["ScrollContainer"]


@final
@deprecations.deprecated(
    since="0.9.2",
    description="Components now have `scroll_x` and `scroll_y` parameters built in.",
)
class ScrollContainer(Component):
    """
    Displays a scroll bar if its content grows too large.

    `ScrollContainer` is a container which displays a scroll bar if its child
    component grows too large. It can scroll vertically and/or horizontally.


    ## Attributes

    `content`: The child component to display inside the `ScrollContainer`.

    `scroll_x`: Controls horizontal scrolling. The default is `"auto"`, which
        means that a scroll bar will be displayed only if it is needed.
        `"always"` displays a scroll bar even if it isn't needed, and
        `"never"` disables horizontal scrolling altogether.

    `scroll_y`: Controls vertical scrolling. The default is `"auto"`, which
        means that a scroll bar will be displayed only if it is needed.
        `"always"` displays a scroll bar even if it isn't needed, and
        `"never"` disables vertical scrolling altogether.

    `sticky_bottom`: If `True`, when the user has scrolled to the bottom and
        the content of the `ScrollContainer` grows larger, the scroll bar
        will automatically scroll to the bottom again.


    ## Examples

    A minimal example of `ScrollContainer` displaying an icon:

    ```python
    rio.ScrollContainer(
        content=rio.Icon("material/castle", width=50, height=50),
        height=10,
    )
    ```
    """

    content: rio.Component
    _: KW_ONLY
    scroll_x: Literal["never", "auto", "always"] = "auto"
    scroll_y: Literal["never", "auto", "always"] = "auto"
    initial_x: float = 0
    initial_y: float = 0
    sticky_bottom: bool = False

    def build(self) -> rio.Component:
        if self.initial_x != 0 or self.initial_y != 0 or self.sticky_bottom:
            raise NotImplementedError()  # FIXME

        return rio.Container(
            self.content,
            scroll_x=self.scroll_x,
            scroll_y=self.scroll_y,
        )
