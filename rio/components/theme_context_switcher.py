from __future__ import annotations

import typing as t

from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "ThemeContextSwitcher",
]


@t.final
class ThemeContextSwitcher(FundamentalComponent):
    """
    A container which can switch between theme contexts ("neutral", "warning",
    ...).

    A `ThemeContextSwitcher` is a container which can switch between so-called
    "theme contexts". The idea behind this is that components sometimes need to
    look different based on where they're being used. For example, text inside
    of a `Button` might have a different color than usual.

    Some components, like `Card`s and `Button`s, automatically apply a different
    context to their children. The `ThemeContextSwitcher` gives you the power to
    do this in your own components as well.

    You can find more details on how theming works in the [Theming Quickstart
    Guide](https://rio.dev/docs/howto/theming-guide).


    ## Attributes

    `content`: The currently displayed component.

    `color`: The color context to switch to.


    ## Examples

    A minimal example of a `ThemeContextSwitcher`:

    ```python
    rio.ThemeContextSwitcher(
        content=rio.Button("Button"),
        color="secondary",
    )
    ```
    """

    content: rio.Component
    color: rio.ColorSet

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "color": self.session.theme._serialize_colorset(self.color),
        }


ThemeContextSwitcher._unique_id_ = "ThemeContextSwitcher-builtin"
