from __future__ import annotations

import typing as t

import rio

from .. import utils
from .component import Component

__all__ = [
    "DialogContainer",
]


@t.final
class DialogContainer(Component):
    build_content: t.Callable[[], Component]
    owning_component_id: int
    is_modal: bool
    is_user_closeable: bool
    on_close: rio.EventHandler[[]]

    def build(self) -> Component:
        return utils.safe_build(self.build_content)

    # Note that this is NOT `_custom_serialize`. Dialog containers are
    # high-level on the Python side, but sent to the client as though they were
    # fundamental. To prevent a whole bunch of custom code in the serializer,
    # this function handles the serialization of dialog containers.
    def serialize(self) -> dict[str, t.Any]:
        return {
            "owning_component_id": self.owning_component_id,
            "is_modal": self.is_modal,
            "is_user_closable": self.is_user_closeable,
        }
