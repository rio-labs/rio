from __future__ import annotations

import asyncio
import typing as t

import imy.docstrings

from . import component, dialog_container

__all__ = ["Dialog"]


T = t.TypeVar("T")


@imy.docstrings.mark_constructor_as_private
class Dialog(t.Generic[T]):
    """
    A handle to a dialog.

    This is the result of `rio.Session.show_custom_dialog`. It allows you to
    programmatically interact with a dialog after showing it. For example, you
    can close the dialog or wait for it to be closed.

    Dialogs can store a result value, which can be retrieved by calling
    `Dialog.wait_for_close`. This allows you to easily wait for the dialog
    to disappear, and also get a return value while you're at it. See the
    example below for details.
    """

    # The component that has created this dialog
    _owning_component: component.Component

    # The root component displayed inside the dialog
    _root_component: dialog_container.DialogContainer

    # If the dialog is gone, this future is set
    _closed_future: asyncio.Future

    # If the dialog has been closed, this is the result value. This is used
    # instead of the future's internal result, because futures cannot be set
    # multiple times.
    _result_value: T | None

    def __init__(self) -> None:
        raise RuntimeError(
            "Dialogs cannot be instantiated directly. To create a dialog, call `await self.session.show_custom_dialog(...)` inside of a component's event handler."
        )

    @classmethod
    def _create(
        cls,
        owning_component: component.Component,
        root_component: dialog_container.DialogContainer,
    ) -> Dialog[T]:
        """
        Internal method to create a new dialog. The class' `__init__` method
        guards against direct instantiation by the user, so this method is used
        to create new instances.
        """
        self = cls.__new__(cls)

        self._owning_component = owning_component
        self._root_component = root_component
        self._closed_future = asyncio.Future()
        self._result_value = None

        return self

    def _close_internal(
        self,
        *,
        result_value: T | None,
    ) -> bool:
        """
        Performs internal housekeeping to close the dialog.

        Returns `True` if the dialog was just closed and `False` if it was
        already closed previously.

        ## Parameters

        `result_value`: An optional value to set as the result of the dialog. If
            the dialog is closed multiple times, the most recent value is used.
        """
        # Save the provided result value, even if the dialog has already been
        # closed.
        self._result_value = result_value

        # If the future is already set, the dialog has already been closed
        if self._closed_future.done():
            return False

        # Set the future to indicate that the dialog has been closed
        self._closed_future.set_result(None)

        # Try to remove the dialog from its owning component. This cannot fail,
        # since the code above guards against closing the dialog multiple times.
        del self._owning_component._owned_dialogs_[self._root_component._id_]

        # Done!
        return True

    async def close(
        self,
        result_value: T | None = None,
    ) -> None:
        """
        Removes the dialog from the screen, if it hasn't been removed already.

        You may optionally provide a `result_value` to set as the result of the
        dialog. This value will be returned by `wait_for_close` when awaited. If
        the dialog is closed multiple times, the most recent value is used.

        ## Parameters

        `result_value`: An optional value to set as the result of the dialog. If
            the dialog is closed multiple times, the most recent value is used.
        """
        # Run the internal cleanup logic. This will also tell us whether the
        # dialog was previously closed, so we can skip the rest of the logic.
        if not self._close_internal(result_value=result_value):
            return

        # The dialog was just discarded on the Python side. Tell the client to
        # also remove it.
        await self._root_component.session._remove_dialog(
            self._root_component._id_,
        )

    @property
    def is_open(self) -> bool:
        """
        Whether the dialog is currently being displayed.

        Returns `True` if the dialog is currently open and `False` if it has
        already been closed. This is the inverse of `is_closed`.
        """
        return not self._closed_future.done()

    @property
    def is_closed(self) -> bool:
        """
        Whether the dialog has already been closed.

        Returns `True` if the dialog has already been closed and `False` if it
        is still open. This is the inverse of `is_open`.
        """
        return self._closed_future.done()

    async def wait_for_close(self) -> T | None:
        """
        Waits until the dialog has been closed. Returns the value that was set
        as the result of the dialog when it was closed.

        If the dialog was closed by any other means than calling `close`, the
        result value is `None`.
        """
        # Wait for the dialog to be closed
        await self._closed_future

        # Return the result value
        return self._result_value
