from __future__ import annotations

from typing import final

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Switcher",
]


@final
class Switcher(FundamentalComponent):
    """
    A container which can switch between different components.

    A `Switcher` is a container which can switch between different components.
    It is commonly used to switch between different views or modes. The
    `content` attribute can be used to change the currently displayed component.


    ## Attributes

    `content`: The currently displayed component.


    ## Examples

    A minimal example of a `Switcher` will be shown:

    ```python
    rio.Switcher(content=rio.Text("Hello, world!"))
    ```

    ## Metadata

    `experimental`: True
    """

    content: rio.Component | None


Switcher._unique_id = "Switcher-builtin"
