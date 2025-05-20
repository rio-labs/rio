from __future__ import annotations

import dataclasses
import typing as t

import rio

from .fundamental_component import FundamentalComponent

__all__ = ["ScrollContainer"]


@t.final
class ScrollContainer(FundamentalComponent):
    """
    Displays a scroll bar if its content grows too large.

    `ScrollContainer` is a container which displays a scroll bar if its child
    component grows too large. It can scroll vertically and/or horizontally.


    ## Attributes

    `content`: The child component to display inside the `ScrollContainer`.

    `scroll_x`: Controls horizontal scrolling. The default is `"auto"`, which
        means that a scroll bar will be displayed only if it is needed.
        `"always"` displays a scroll bar even if it isn't needed, and
        `"never"` disables horizontal scrolling altogether. (Note that overlay
        scrollbars may be invisible even when set to `"always"`.)

    `scroll_y`: Controls vertical scrolling. The default is `"auto"`, which
        means that a scroll bar will be displayed only if it is needed.
        `"always"` displays a scroll bar even if it isn't needed, and
        `"never"` disables vertical scrolling altogether. (Note that overlay
        scrollbars may be invisible even when set to `"always"`.)

    `initial_x`: The initial horizontal scroll position. The value should be
        between `0` and `1`, where `0` is the leftmost position and `1` is
        the rightmost position.

    `initial_y`: The initial vertical scroll position. The value should be
        between `0` and `1`, where `0` is the topmost position and `1` is
        the bottommost position.

    `reserve_space_y`: Whether to reserve some space for the vertical
        scroll bar when it's not visible. This prevents the content from
        jumping around whenever the scroll bar appears or disappears.

    `sticky_bottom`: If `True`, when the user has scrolled to the bottom and
        the content of the `ScrollContainer` grows larger, the scroll bar
        will automatically scroll to the bottom again.


    ## Examples

    A minimal example of `ScrollContainer` displaying an icon:

    ```python
    rio.ScrollContainer(
        content=rio.Icon("material/castle", min_width=50, min_height=50),
        min_height=10,
    )
    ```
    """

    content: rio.Component
    _: dataclasses.KW_ONLY
    scroll_x: t.Literal["never", "auto", "always"] = "auto"
    scroll_y: t.Literal["never", "auto", "always"] = "auto"
    initial_x: float = 0
    initial_y: float = 0
    reserve_space_y: bool = False
    sticky_bottom: bool = False


ScrollContainer._unique_id_ = "ScrollContainer-builtin"
