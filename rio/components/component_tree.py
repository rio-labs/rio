from __future__ import annotations

from dataclasses import KW_ONLY
from typing import Any

import rio

from .fundamental_component import FundamentalComponent

__all__ = ["ComponentTree"]


class ComponentTree(FundamentalComponent):
    """
    Note: This component makes not attempt to request the correct amount of
    space. Specify a width/height manually, or make sure it's in a properly
    sized parent.

    ## Metadata

    public: False
    """

    _: KW_ONLY

    # Triggered whenever the user selects a component in the tree. The passed
    # value is the component's ID.
    on_select_component: rio.EventHandler[int] = None

    async def _on_message(self, msg: Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg
        selected_component_id = msg["selectedComponentId"]

        # Trigger the press event
        await self.call_event_handler(
            self.on_select_component, selected_component_id
        )

        # Refresh the session
        await self.session._refresh()


ComponentTree._unique_id = "ComponentTree-builtin"
