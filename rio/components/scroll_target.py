from __future__ import annotations

import dataclasses
import typing as t

from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = ["ScrollTarget"]


@t.final
class ScrollTarget(FundamentalComponent):
    """
    Allows browsers to scroll to a specific component via URL fragment.

    `ScrollTarget` is a container which can be referenced by a URL fragment,
    which allows browsers to scroll to it when the page is loaded. For example,
    if your website contains a `ScrollTarget` with the ID `"my-section"`, then a
    browser visiting `https://your.website/#my-section` will immediately scroll
    it into view.

    When the mouse cursor is hovering over the `ScrollTarget`, it displays a `¶`
    symbol on its right side. Users can click this symbol to copy the URL to
    their clipboard. This symbol can be customized or removed through the
    `copy_button_content` parameter.


    ## Attributes

    `id`: The ID of the `ScrollTarget`. This must be unique among all
        `ScrollTarget`s on the page.

    `content`: The child component to display inside the `ScrollTarget`.

    `copy_button_content`: The text or component to use as the "Copy URL to
        clipboard" button. Setting this to `None` removes the button entirely.

    `copy_button_spacing`: The amount of empty space between the `content` and
        `copy_button_content`.


    ## Examples

    A minimal example of `ScrollTarget` displaying a heading:

    ```python
    rio.ScrollTarget(
        id="chapter-1",
        content=rio.Text("Chapter 1", style="heading1"),
    )
    ```

    ## Metadata

    `experimental`: True
    """

    id: str
    content: rio.Component | None = None
    _: dataclasses.KW_ONLY
    copy_button_content: str | rio.Component | None = "¶"
    copy_button_spacing: float = 0.5

    def _custom_serialize_(self) -> JsonDoc:
        button_content = self.copy_button_content

        return {
            "copy_button_content": button_content._id_
            if isinstance(button_content, rio.Component)
            else None,
            "copy_button_text": button_content
            if isinstance(button_content, str)
            else None,
        }


ScrollTarget._unique_id_ = "ScrollTarget-builtin"
