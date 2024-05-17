from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import Literal, final

from uniserde import JsonDoc

import rio.docs

from .fundamental_component import FundamentalComponent

__all__ = [
    "Popup",
    "PopupOpenOrCloseEvent",
]


@final
@rio.docs.mark_constructor_as_private
@dataclass
class PopupOpenOrCloseEvent:
    """
    Holds information regarding a popup open or close event.

    This is a simple dataclass that stores useful information for when the user
    opens or closes a popup. You'll typically receive this as argument in
    `on_open_or_close` events.
    """

    is_open: bool


@final
class Popup(FundamentalComponent):
    """
    A container which floats above other components.

    Popups are containers which float above the page when open. This allows you
    to keep your app clean by default, but present additional information or
    controls when needed.

    They take two children: The `anchor` is always visible and positions the
    popup. The `content` is located inside the popup and is only visible when
    the popup is open.

    The location popups appear at can be customized using the `direction`,
    `alignment` and `gap` attributes. Popups wil do their best to honor those
    settings, but deviate if necessary to ensure they don't go off-screen.


    ## Attributes

    `anchor`: A component which is always visible and positions the popup.

    `content`: A component which is only visible when the popup is open.

    `direction`: The direction into which the popup opens.

    `alignment`: The alignment of the popup within the anchor. If the popup
        opens to the left or right, this is the vertical alignment, with `0`
        being the top and `1` being the bottom. If the popup opens to the top or
        bottom, this is the horizontal alignment, with `0` being the left and
        `1` being the right. Has no effect if the popup opens centered.

    `gap`: How much space to leave between the popup and the anchor. Has no
        effect popup opens centered.

    `is_open`: Whether the popup is currently open.

    `on_open_or_close`: Triggered when the popup is opened or closed.
    """

    # TODO: Add example to docstring

    anchor: rio.Component
    content: rio.Component
    _: KW_ONLY
    color: rio.ColorSet = "neutral"
    direction: Literal["left", "top", "right", "bottom", "center"] = "center"
    alignment: float = 0.5
    gap: float = 0.8
    is_open: bool = False
    on_open_or_close: rio.EventHandler[PopupOpenOrCloseEvent] = None

    def _validate_delta_state_from_frontend(self, delta_state: JsonDoc) -> None:
        if not set(delta_state) <= {"is_open"}:
            raise AssertionError(
                f"Frontend tried to change `{type(self).__name__}` state: {delta_state}"
            )

    async def _call_event_handlers_for_delta_state(
        self, delta_state: JsonDoc
    ) -> None:
        # Trigger on_open_or_close event
        try:
            is_open = delta_state["is_open"]
        except KeyError:
            pass
        else:
            assert isinstance(is_open, bool), is_open
            await self.call_event_handler(
                self.on_open_or_close,
                PopupOpenOrCloseEvent(is_open),
            )

    def _custom_serialize(self) -> JsonDoc:
        return {
            "color": self.session.theme._serialize_colorset(self.color),
        }


Popup._unique_id = "Popup-builtin"
