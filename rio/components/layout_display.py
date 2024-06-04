from __future__ import annotations

from dataclasses import KW_ONLY
from typing import *  # type: ignore

from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "LayoutDisplay",
]


@final
class LayoutDisplay(FundamentalComponent):
    component_id: int

    _: KW_ONLY

    on_component_change: rio.EventHandler[int] = None

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


LayoutDisplay._unique_id = "LayoutDisplay-builtin"
