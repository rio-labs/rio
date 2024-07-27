from __future__ import annotations

from typing import *  # type: ignore

from .. import utils
from .component import Component

__all__ = [
    "DialogContainer",
]


@final
class DialogContainer(Component):
    owning_component_id: int
    build_content: Callable[[], Component]

    def build(self) -> Component:
        return utils.safe_build(self.build_content)

    # Note that this is NOT `_custom_serialize`. Dialog containers are
    # high-level on the Python side, but sent to the client as though they were
    # fundamental. To prevent a whole bunch of custom code in the serializer,
    # this function handles the serialization of dialog containers.
    def serialize(self) -> dict[str, Any]:
        return {
            "owningComponentId": self.owning_component_id,
        }
