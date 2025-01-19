from __future__ import annotations

import dataclasses

from uniserde import JsonDoc

import rio

from ...components.fundamental_component import FundamentalComponent

__all__ = ["ComponentTree"]


class ComponentTree(FundamentalComponent):
    """
    Note: This component makes no attempt to request the correct amount of
    space. Specify a width/height manually, or make sure it's in a properly
    sized parent.

    ## Metadata

    `public`: False
    """

    component_id: int  # This can be invalid. The component must deal with it.

    _: dataclasses.KW_ONLY

    # Triggered whenever the user selects a component in the tree. The passed
    # value is the component's ID.
    on_select_component: rio.EventHandler[int] = None

    def _validate_delta_state_from_frontend(self, delta_state: JsonDoc) -> None:
        if not set(delta_state) <= {"component_id"}:
            raise AssertionError(
                f"Frontend tried to change `{type(self).__name__}` state: {delta_state}"
            )

    async def _call_event_handlers_for_delta_state(
        self, delta_state: JsonDoc
    ) -> None:
        # Trigger the change event
        try:
            new_id = delta_state["component_id"]
        except KeyError:
            pass
        else:
            assert isinstance(new_id, int), new_id
            await self.call_event_handler(self.on_select_component, new_id)


ComponentTree._unique_id_ = "ComponentTree-builtin"
