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
    TODO


    ## Attributes

    `content`: The currently displayed component.


    ## Examples

    A minimal example of a `Switcher` will be shown:

    ```python
    rio.Switcher(content=rio.Text("Hello, world!"))
    ```


    ## Metadata

    `public`: False

    `experimental`: True
    """

    content: rio.Component | None


Switcher._unique_id = "Switcher-builtin"
