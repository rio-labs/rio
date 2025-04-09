from __future__ import annotations

import typing as t

import imy.docstrings

import rio

from .. import utils
from .component import Component

__all__ = [
    "DialogContainer",
]


@t.final
@imy.docstrings.mark_as_private
class DialogContainer(Component):
    build_content: t.Callable[[], Component]
    owning_component_id: int
    is_modal: bool
    is_user_closable: bool
    on_close: rio.EventHandler[[]]
    style: t.Literal["default", "custom"] = "default"

    def build(self) -> Component:
        # Build the content
        content = utils.safe_build(self.build_content)

        # Apply the default dialog styling, if requested
        if self.style == "default":
            theme = self.session.theme

            content = rio.Rectangle(
                content=rio.Container(
                    rio.ThemeContextSwitcher(content, "neutral"),
                    margin=1.5,
                ),
                fill=theme.neutral_color,
                corner_radius=theme.corner_radius_medium,
                shadow_radius=1.8,
                shadow_offset_y=1.0,
                align_x=0.5,
                align_y=0.4,
            )

        # Done
        return content

    # Note that this is NOT `_custom_serialize_`. Dialog containers are
    # high-level on the Python side, but sent to the client as though they were
    # fundamental. To prevent a whole bunch of custom code in the serializer,
    # this function handles the serialization of dialog containers.
    def serialize(self) -> dict[str, t.Any]:
        return {
            "owning_component_id": self.owning_component_id,
            "is_modal": self.is_modal,
            "is_user_closable": self.is_user_closable,
        }
