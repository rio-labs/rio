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
        Removes the dialog from the screen. Has no effect if the dialog has
        already been removed.
        """
        # Dialogs are registered with their owning component. Remove them from
        # there.
        #
        # First, try to get the owning component from the session. Since it
        # holds a reference to the dialog, if it can't be found, the dialog must
        # have already been removed previously.
        session = self._root_component.session
        owning_component = session._weak_components_by_id.get(
            self._root_component._id,
        )

        if owning_component is None:
            return

        # Try to remove the dialog from its owning component. This can of course
        # fail if the dialog has already been removed.
        try:
            del owning_component._owned_dialogs_[self._root_component._id]
        except KeyError:
            return

        # The dialog was just discarded on the Python side. Tell teh client to
        # also remove it.
        await self._root_component.session._remove_dialog(
            self._root_component._id,
        )
