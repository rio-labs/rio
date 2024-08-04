from __future__ import annotations

from . import component, dialog_container


class Dialog:
    # The component that has created this dialog
    _owning_component: component.Component

    # The root component displayed inside the dialog
    _root_component: dialog_container.DialogContainer

    def __init__(self) -> None:
        raise RuntimeError(
            "Dialogs cannot be instantiated directly. To create a dialog, call `self.show_custom_dialog` inside of a component's event handler."
        )

    def _cleanup(self) -> None:
        # Try to remove the dialog from its owning component. This can fail if
        # the dialog has already been removed.
        try:
            del self._owning_component._owned_dialogs_[self._root_component._id]
        except KeyError:
            return

    async def close(self) -> None:
        """
        Removes the dialog from the screen. Has no effect if the dialog has
        already been previously closed.
        """
        self._cleanup()

        # The dialog was just discarded on the Python side. Tell the client to
        # also remove it.
        await self._root_component.session._remove_dialog(
            self._root_component._id,
        )
