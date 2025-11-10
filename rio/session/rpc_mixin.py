from __future__ import annotations

import asyncio
import logging
import time
import typing as t

import unicall.json_rpc

import rio

from ..components import fundamental_component, dialog_container
from ..transports import (
    AbstractTransport,
    TransportClosedIntentionally,
    TransportInterrupted,
)
from .. import utils, serialization


RpcError = unicall.RpcError


class SessionRpcMixin(unicall.Unicall):
    def __init__(self, transport):
        super().__init__(
            transport=unicall.json_rpc.JsonRpcTransport(
                send=self.__send_message,
                receive=self.__receive_message,
                serde=serialization.json_serde,
                parameter_format="list",
                json_dumps=serialization.serialize_json,
            )
        )

        # The current transport, though it may be closed
        self._rio_transport = transport

        # Event indicating whether there is an open connection to the client.
        # This starts off set, since the session is created with a valid
        # transport.
        self._is_connected_event = asyncio.Event()
        if not transport.is_closed:
            self._is_connected_event.set()

    async def __send_message(self, message: str) -> None:
        await self._rio_transport.send_if_possible(message)

    async def __receive_message(self) -> str:
        # Sessions don't immediately die if the connection is interrupted, they
        # can be reconnected. We will hide this fact from unicall because
        # unicall cancels any running RPC functions when the transport is
        # closed. We wouldn't want something like a `_component_message()` to be
        # interrupted halfway through.
        while True:
            # Wait until we have a connected transport
            await self._is_connected_event.wait()

            try:
                return await self._rio_transport.receive()
            except TransportInterrupted:
                self._is_connected_event.clear()
                self._app_server._disconnected_sessions[self] = time.monotonic()
            except TransportClosedIntentionally:
                self.close()

                while True:
                    await asyncio.sleep(999999)

    @property
    def _is_connected(self) -> bool:
        """
        Returns whether there is an active connection to a client
        """
        return not self._rio_transport.is_closed

    async def _replace_rio_transport(
        self, transport: AbstractTransport
    ) -> None:
        assert not transport.is_closed

        # Close the current transport
        await self._rio_transport.close()

        # Remember the new transport
        self._rio_transport = transport

        self._is_connected_event.set()
        self._app_server._disconnected_sessions.pop(self, None)

    @unicall.remote(
        name="applyTheme",
        await_response=False,
    )
    async def _remote_apply_theme(
        self,
        css_variables: dict[str, str],
        theme_variant: t.Literal["light", "dark"],
    ) -> None:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="setTitle",
        await_response=False,
    )
    async def _remote_set_title(self, title: str) -> None:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="setKeyboardFocus",
        await_response=False,
    )
    async def _remote_set_keyboard_focus(self, component_id: int) -> None:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="updateComponentStates",
        await_response=False,
    )
    async def _remote_update_component_states(
        self,
        # Maps component ids to serialized components. The components may be
        # partial, i.e. any property may be missing.
        delta_states: dict[int, t.Any],
        # Tells the client to make the given component the new root component.
        root_component_id: int | None,
    ) -> None:
        """
        Replace all components in the UI with the given one.
        """
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="evaluateJavaScript",
        await_response=False,
    )
    async def _evaluate_javascript(self, java_script_source: str) -> t.Any:
        """
        Evaluate the given JavaScript code on the client.

        The code is run as the body of a function, i.e.

        - `return` statements are allowed

        - Variables are neatly contained in a scope and don't pollute the global
          scope
        """
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="evaluateJavaScriptAndGetResult",
        await_response=True,
    )
    async def _evaluate_javascript_and_get_result(
        self,
        java_script_source: str,
    ) -> t.Any:
        """
        Evaluate the given JavaScript code in the client and return the result.

        The code is run as the body of a function, i.e.

        - `return` statements are allowed and must be used to receive a result
          other than `None`

        - Variables are neatly contained in a scope and don't pollute the global
          scope
        """
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="requestFileUpload",
        await_response=False,
    )
    async def _request_file_upload(
        self,
        upload_url: str,
        file_types: list[str] | None,
        multiple: bool,
    ) -> None:
        """
        Tell the client to upload a file to the server.

        If `file_types` is provided, the strings should be file extensions,
        without any leading dots. E.g. `["pdf", "png"]`.
        """
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(name="setUserSettings", await_response=False)
    async def _remote_set_user_settings(
        self, delta_settings: dict[str, t.Any]
    ) -> None:
        """
        Persistently store the given key-value pairs at the user. The values
        have to be jsonable.

        Any keys not present here are still preserved. Thus the function
        effectively behaves like `dict.update`.
        """
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(name="registerFont", await_response=False)
    async def _remote_register_font(
        self,
        name: str,
        urls: list[str],
        file_metas: list[str],
        descriptors: list[dict[str, str]],
    ) -> None:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(name="changeUrl", await_response=False)
    async def _remote_url_change(self, url: str, replace: bool) -> None:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="closeSession",
        await_response=False,
    )
    async def _remote_close_session(self) -> None:
        raise NotImplementedError  # pragma: no cover

    def _try_get_component_for_message(
        self, component_id: int
    ) -> rio.Component | None:
        """
        Attempts to get the component referenced by `component_id`. Returns
        `None` if there is no such component. This can happen during normal
        opration, e.g. because a component has been deleted while the message
        was in flight.
        """

        try:
            return self._weak_components_by_id[component_id]
        except KeyError:
            logging.warning(
                f"Encountered message for unknown component {component_id}. (The component might have been deleted in the meantime.)"
            )
            return None

    @unicall.local(name="componentStateUpdate")
    async def _component_state_update(
        self,
        component_id: int,
        delta_state: t.Any,
    ) -> None:
        # Get the component
        component = self._try_get_component_for_message(component_id)

        if component is None:
            return

        assert isinstance(
            component, fundamental_component.FundamentalComponent
        ), component

        # Update the component's state
        component._validate_delta_state_from_frontend(delta_state)
        component._apply_delta_state_from_frontend(delta_state)
        await component._call_event_handlers_for_delta_state(delta_state)

        # Trigger a refresh. The component itself doesn't need to rebuild, but
        # other components with a attribute binding to the changed values might.
        await self._refresh()

    @unicall.local(name="componentMessage")
    async def _component_message(
        self,
        component_id: int,
        payload: t.Any,
    ) -> None:
        # Get the component
        component = self._try_get_component_for_message(component_id)

        if component is None:
            return

        # Let the component handle the message
        await component._on_message_(payload)

    @unicall.local(name="dialogClosed")
    async def _dialog_closed(self, dialog_root_component_id: int) -> None:
        # Fetch and remove the dialog itself, while still not succumbing to
        # network lag
        try:
            dialog_cont = self._weak_components_by_id[dialog_root_component_id]
        except KeyError:
            return

        assert isinstance(dialog_cont, dialog_container.DialogContainer), (
            dialog_cont
        )

        # Fetch the owning component
        try:
            dialog_owner = self._weak_components_by_id[
                dialog_cont.owning_component_id
            ]
        except KeyError:
            # Don't die to network lag
            return

        # Fetch the Dialog object and mark it as closed
        try:
            dialog = dialog_owner._owned_dialogs_[dialog_root_component_id]
        except KeyError:
            # Don't die to network lag
            return

        dialog._close_internal(result_value=None)

        # Trigger the dialog's close event
        await self._call_event_handler(
            dialog_cont.on_close,
            refresh=True,
        )

    @unicall.local(name="openUrl")
    async def _open_url(self, url: str) -> None:
        # Case: Running as website
        #
        # If running in a browser, JS can take care of changing the URL or
        # opening a new tab. The only reason why the frontend would tell us
        # to open the url is because it's a local url.
        #
        # (Note: Of course an attacker could send us an external url to
        # open, but `navigate_to` has to handle that gracefully anyway.)
        if self.running_as_website:
            self.navigate_to(url)
            return

        # Case: Running in a window.
        yarl_url = rio.URL(url)
        del url

        # If running_in_window, local urls are *always* navigated to, even if
        # they're meant to be opened in a new tab. The `run_in_window` code
        # isn't designed to handle multiple sessions, so we can't open a new
        # tab or a 2nd window.
        try:
            utils.url_relative_to_base(yarl_url, self._base_url)

        # And if it's an external url, it must be opened in a web browser.
        except ValueError:
            import webbrowser

            webbrowser.open(str(yarl_url))

        # Local URL
        else:
            self.navigate_to(yarl_url)

    @unicall.local(name="ping")
    async def _ping(self, ping: str) -> str:
        return "pong"

    @unicall.local(name="onUrlChange")
    async def _on_url_change(self, new_url: str) -> None:
        """
        Called by the client when the page changes. (This happens when the user
        presses the "back" button in the browser.)
        """
        self.navigate_to(
            new_url,
            # Since the URL change originated in the browser, it's actually
            # already recorded in the history. We don't want to create an
            # additional entry, so we'll simply use `replace` to overwrite it
            # with itself.
            replace=True,
        )

    @unicall.local(name="onWindowSizeChange")
    async def _on_window_size_change(
        self, new_width: float, new_height: float
    ) -> None:
        """
        Called by the client when the window is resized.
        """
        # Update the stored window size
        self.window_width = new_width
        self.window_height = new_height

        # Trigger the `on_page_size_change` event
        for (
            component,
            callbacks,
        ) in self._on_window_size_change_callbacks.items():
            for callback in callbacks:
                self.create_task(
                    self._call_event_handler(callback, component, refresh=True),
                    name="`on_on_window_size_change` event handler",
                )

    @unicall.local(name="onComponentSizeChange")
    async def _on_component_size_change(
        self, component_id: int, new_width: float, new_height: float
    ) -> None:
        """
        Called by the client when a component is resized.
        """
        component = self._weak_components_by_id.get(component_id)
        if component:
            resize_event = rio.ComponentResizeEvent(new_width, new_height)

            for handler, _ in component._rio_event_handlers_[
                rio.event.EventTag.ON_RESIZE
            ]:
                self._call_event_handler_sync(handler, component, resize_event)

    @unicall.local(name="onFullscreenChange")
    async def _on_fullscreen_change(self, fullscreen: bool) -> None:
        """
        Called by the client when the window is (un-)fullscreened.
        """
        self._is_fullscreen = fullscreen

    @unicall.local(name="onMaximizedChange")
    async def _on_maximized_change(self, maximized: bool) -> None:
        """
        Called by the client when the window is (un-)maximized.
        """
        self._is_maximized = maximized

    @unicall.remote(
        name="setClipboard",
        await_response=False,
    )
    async def _remote_set_clipboard(self, text: str) -> None:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="getClipboard",
        await_response=True,
    )
    async def _remote_get_clipboard(self) -> str:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="getComponentLayouts",
        await_response=True,
    )
    async def _remote_get_component_layouts(
        self, component_ids: list[int]
    ) -> list[dict[str, t.Any] | None]:
        raise NotImplementedError()  # pragma: no cover

    @unicall.remote(
        name="getUnittestClientLayoutInfo",
        await_response=True,
    )
    async def __get_unittest_client_layout_info(
        self,
    ) -> t.Any:
        raise NotImplementedError()  # pragma: no cover

    @unicall.remote(
        name="pickComponent",
        await_response=False,
    )
    async def _pick_component(self) -> None:
        """
        Lets the user select a component in the ComponentTree by clicking on it
        in the DOM.
        """
        raise NotImplementedError()  # pragma: no cover

    @unicall.remote(
        name="removeDialog",
        await_response=False,
    )
    async def _remove_dialog(self, root_component_id: int) -> None:
        """
        Removes the dialog with the given root component id, destroying the
        component and its children.
        """
        raise NotImplementedError()  # pragma: no cover
