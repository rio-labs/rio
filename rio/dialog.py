from __future__ import annotations

from . import component


class Dialog:
    # The root component displayed inside the dialog.
    _root_component: component.Component

    def __init__(self) -> None:
        raise RuntimeError(
            "Dialogs cannot be instantiated directly. To create a dialog, call `self.show_custom_dialog` inside of a component's event handler."
        )

    async def remove(self) -> None:
        """
        Removes the dialog from the screen.
        """
        # Dialogs are registered with their owning component. Remove them from
        # there.
        session = self._root_component.session
        owning_component = session._weak_components_by_id.get(
            self._root_component._id,
        )
        assert owning_component is not None

        # Try to remove the dialog from its owning component. If this fails, the
        # dialog has already been removed before
        try:
            del owning_component._owned_dialogs_[self._root_component._id]
        except KeyError:
            return

        # Tell the client to remove the dialog
        await self._root_component.session._remove_dialog(
            self._root_component._id,
        )
