from __future__ import annotations

import typing as t

from uniserde import JsonDoc

import rio

from .. import icon_registry
from .fundamental_component import FundamentalComponent

__all__ = [
    "Link",
]


@t.final
class Link(FundamentalComponent):
    """
    Navigates to a page or URL when pressed.

    `Link`s display a short text, or an arbitrary component, and navigate to a
    page or URL when clicked.


    ## Attributes

    `child_text`: The text to display inside the link.

    `icon`: Optionally an icon to display next to the text. This is only visible
        if the content is a string.

    `child_component`: The component to display inside the link.

    `target_url`: The page or URL to navigate to when clicked.

    `open_in_new_tab`: Whether to open the link in a new tab. Defaults to
        `False`.


    ## Examples

    This minimal example will display a simple text and navigate away when
    pressed.

    ```python
    rio.Link("Click me!", "https://example.com")
    ```

    You can also use a component as the child of the link:

    ```python
    rio.Link(
        rio.Button("Click me!"),
        "https://example.com",
    )
    ```
    """

    # Exactly one of these will be set, the other `None`
    child_text: str | None
    child_component: rio.Component | None
    target_url: rio.URL | str
    open_in_new_tab: bool
    icon: str | None

    # The serializer can't handle Union types. Override the constructor, so it
    # splits the child into two values
    def __init__(
        self,
        content: rio.Component | str,
        target_url: rio.URL | str,
        *,
        icon: str | None = None,
        open_in_new_tab: bool = False,
        key: str | int | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
    ) -> None:
        """
        ## Parameters

        `content`: The text or component to display inside the link.

        `target_url`: The page or URL to navigate to when clicked.
        """
        super().__init__(
            key=key,
            margin=margin,
            margin_x=margin_x,
            margin_y=margin_y,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
            align_x=align_x,
            align_y=align_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
        )

        if isinstance(content, str):
            self.child_text = content
            self.child_component = None
        else:
            self.child_text = None
            self.child_component = content

        self.target_url = target_url
        self.open_in_new_tab = open_in_new_tab
        self.icon = icon

        self._properties_set_by_creator_.update(
            ("child_text", "child_component")
        )

    def __post_init__(self) -> None:
        # Verify that the icon exists. This makes sure any crashes happen
        # immediately, rather than during the next refresh.
        if self.icon is not None:
            icon_registry.get_icon_svg(self.icon)

    def _custom_serialize_(self) -> JsonDoc:
        # Get the full URL to navigate to
        target_url_absolute = self.session.active_page_url.join(
            rio.URL(self.target_url)
        )

        # Serialize everything
        return {
            "targetUrl": str(target_url_absolute),
        }


Link._unique_id_ = "Link-builtin"
