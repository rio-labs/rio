from __future__ import annotations

import webbrowser
from typing import Any, Literal, final

from uniserde import JsonDoc

import rio

from .. import common
from .fundamental_component import FundamentalComponent

__all__ = [
    "Link",
]


@final
class Link(FundamentalComponent):
    """
    Navigates to a page or URL when clicked.

    `Link`s display a short text, or arbitrary component, and navigate to a page
    or URL when clicked.


    ## Attributes

    `child_text`: The text to display inside the link.

    `child_component`: The component to display inside the link.

    `target_url`: The page or URL to navigate to when clicked.

    `open_in_new_tab`: Whether to open the link in a new tab. Defaults to `False`.


    ## Examples

    This minimal example will simply display a link with the URL
    "https://example.com" and a text "Click me!":

    ```python
    rio.Link("Click me!", "https://example.com")
    ```
    """

    # Exactly one of these will be set, the other `None`
    child_text: str | None
    child_component: rio.Component | None
    target_url: rio.URL | str
    open_in_new_tab: bool

    # The serializer can't handle Union types. Override the constructor, so it
    # splits the child into two values
    def __init__(
        self,
        content: rio.Component | str,
        target_url: rio.URL | str,
        *,
        open_in_new_tab: bool = False,
        key: str | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        width: float | Literal["natural", "grow"] = "natural",
        height: float | Literal["natural", "grow"] = "natural",
        align_x: float | None = None,
        align_y: float | None = None,
    ):
        """
        ## Parameters
            content: The text or component to display inside the link.

            target_url: The page or URL to navigate to when clicked.
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
            width=width,
            height=height,
            align_x=align_x,
            align_y=align_y,
        )

        if isinstance(content, str):
            self.child_text = content
            self.child_component = None
        else:
            self.child_text = None
            self.child_component = content

        self.target_url = target_url
        self.open_in_new_tab = open_in_new_tab

        self._properties_set_by_creator_.update(
            ("child_text", "child_component")
        )

    async def _on_message(self, msg: Any) -> None:
        assert isinstance(msg, dict), msg

        if "page" in msg:
            # Navigate to the link. Note that this allows the client to inject
            # a, possibly malicious, link. This is fine, because the client can
            # do so anyway, simply by changing the URL in the browser. Thus the
            # server has to be equipped to handle malicious page URLs anyway.
            target_page = msg["page"]
            self.session.navigate_to(target_page)
        elif self.session.running_in_window:
            # If running in a window, clicking a link shouldn't open it in the
            # app window. Instead, we receive a message telling us to open the
            # link in browser.
            target_url = msg["open"]
            webbrowser.open(target_url)

    def _custom_serialize(self) -> JsonDoc:
        # Get the full URL to navigate to
        target_url_absolute = self.session.active_page_url.join(
            rio.URL(self.target_url)
        )

        # Is the link a URL or page?
        #
        # The URL is a page, if it starts with the session's base URL
        try:
            common.make_url_relative(
                self.session._base_url,
                target_url_absolute,
            )
        except ValueError:
            is_page = False
        else:
            is_page = True

        # Serialize everything
        return {
            "targetUrl": str(target_url_absolute),
            "isPage": is_page,
        }


Link._unique_id = "Link-builtin"
