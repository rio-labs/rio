from __future__ import annotations

from dataclasses import KW_ONLY
from typing import final

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Switcher",
]


@final
class Switcher(FundamentalComponent):
    """
    Smoothly transitions between components.

    The `Switcher` component is a container which can display one component at a
    time. What makes it useful, is that when you change the `content` attribute,
    rather than instantly swapping the displayed component, it will smoothly
    transition between the two.

    Moreover, whenever the content's size changes, the `Switcher` will
    smoothly resize to match the new size. This means you can use switchers
    to smoothly transition between components of different sizes.

    `content` may also be `None`, in which case the `Switcher` won't display
    anything. This in turn allows you to animate the appearance or disappearance
    of a component, e.g. for a sidebar.


    ## Attributes

    `content`: The component to display inside the switcher. If `None`, the
        switcher will be empty.

    `transition_time`: How many seconds it should take for the switcher to
        transition between components and sizes.


    ## Metadata

    `experimental`: True
    """

    content: rio.Component | None

    _: KW_ONLY

    transition_time: float = 0.35


Switcher._unique_id = "Switcher-builtin"
