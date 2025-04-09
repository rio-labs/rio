from __future__ import annotations

import dataclasses
import typing as t

from uniserde import JsonDoc

import rio

from ...components.fundamental_component import FundamentalComponent

__all__ = [
    "LayoutDisplay",
]


@t.final
class LayoutDisplay(FundamentalComponent):
    component_id: int  # This can be invalid. The component must deal with it.

    _: dataclasses.KW_ONLY

    max_requested_height: float = 1
    on_component_change: rio.EventHandler[int] = None
    on_layout_change: rio.EventHandler[[]] = None

    async def _on_message_(self, msg: t.Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg
        assert msg["type"] == "layoutChange", msg

        # Trigger the event handler
        await self.call_event_handler(self.on_layout_change)

    def _validate_delta_state_from_frontend(self, delta_state: JsonDoc) -> None:
        if not set(delta_state) <= {"component_id"}:
            raise AssertionError(
                f"Frontend tried to change `{type(self).__name__}` state: {delta_state}"
            )

    async def _call_event_handlers_for_delta_state(
        self, delta_state: JsonDoc
    ) -> None:
        # Trigger on_change event
        try:
            new_value = delta_state["component_id"]
        except KeyError:
            pass
        else:
            assert isinstance(new_value, int), new_value
            await self.call_event_handler(self.on_component_change, new_value)


LayoutDisplay._unique_id_ = "LayoutDisplay-builtin"
