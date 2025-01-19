from __future__ import annotations

import dataclasses
import typing as t

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Switcher",
]


@t.final
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


    ## Example

    This example showcases a simple switcher component that allows users to
    control the visibility of a content element. The content element is a
    rectangle that appears or disappears when the button is pressed.

    ```python
    class MyComponent(rio.Component):
        show_content: bool = False

        def _on_press(self) -> None:
            self.show_content = not self.show_content

        def build(self) -> rio.Component:
            # Make the content appear or disappear based on the show_content
            # attribute
            content = (
                rio.Rectangle(
                    fill=rio.Color.from_hex("00bf63"),
                    min_height=12,
                )
                if self.show_content
                else None  # No content if show_content is False
            )
            return rio.Column(
                rio.Button("Show content", on_press=self._on_press),
                # Switcher to show/hide content
                rio.Switcher(
                    content=content,
                ),
                align_y=0.5,
                align_x=0.5,
            )
    ```
    ## Metadata

    `experimental`: True
    """

    content: rio.Component | None

    _: dataclasses.KW_ONLY

    transition_time: float = 0.35


Switcher._unique_id_ = "Switcher-builtin"
