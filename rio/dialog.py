from __future__ import annotations

from . import component


class Dialog:
    # The component that has created this dialog
    _owning_component: component.Component

    # The root component displayed inside the dialog
    _root_component: component.Component

    def __init__(self) -> None:
        raise RuntimeError(
            "Dialogs cannot be instantiated directly. To create a dialog, call `self.show_custom_dialog` inside of a component's event handler."
        )

    async def remove(self) -> None:
        """
        Removes the dialog from the screen. Has no effect if the dialog has
        already been removed.
        """
        # Try to remove the dialog from its owning component. This can fail if
        # the dialog has already been removed.
        try:
            del self._owning_component._owned_dialogs_[self._root_component._id]
        except KeyError:
            return

        # The dialog was just discarded on the Python side. Tell the client to
        # also remove it.
        await self._root_component.session._remove_dialog(
            self._root_component._id,
        )
