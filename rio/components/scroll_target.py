from __future__ import annotations

import rio

from .fundamental_component import FundamentalComponent

__all__ = ["ScrollTarget"]


class ScrollTarget(FundamentalComponent):
    """
    # ScrollTarget

    Allows browsers to scroll to a specific component via URL fragment.

    `ScrollTarget` is a container which can be referenced by a URL fragment,
    which allows browsers to scroll to it when the page is loaded. For example,
    if your website contains a `ScrollTarget` with the ID `"my-section"`, then a
    browser visiting `https://your.website/#my-section` will immediately scroll
    it into view.


    ## Attributes:

    `id`: The ID of the `ScrollTarget`. This must be unique among all
            `ScrollTarget`s on the page.

    `content`: The child component to display inside the `ScrollTarget`.


    ## Example:

    A minimal example of `ScrollTarget` displaying an icon:

    #TODO: Better example
    ```python
    rio.ScrollTarget(
        id="my-section",
        content=rio.Icon("castle", width=50, height=50),
    )
    ```
    """

    id: str
    content: rio.Component | None = None


ScrollTarget._unique_id = "ScrollTarget-builtin"
