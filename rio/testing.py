import asyncio
import typing as t

import ordered_set
import starlette.datastructures
import typing_extensions as te
from uniserde import JsonDoc

import rio

from . import data_models
from .app_server import TestingServer
from .transports import MessageRecorderTransport, TransportInterrupted

__all__ = ["TestClient"]


T = t.TypeVar("T")
C = t.TypeVar("C", bound=rio.Component)


class TestClient:
    @t.overload
    def __init__(
        self,
        app: rio.App,
        *,
        running_in_window: bool = False,
        user_settings: JsonDoc = {},
        active_url: str = "/",
        use_ordered_dirty_set: bool = False,
    ): ...

    @t.overload
    def __init__(
        self,
        build: t.Callable[[], rio.Component] = rio.Spacer,
        *,
        app_name: str = "mock-app",
        default_attachments: t.Iterable[object] = (),
        running_in_window: bool = False,
        user_settings: JsonDoc = {},
        active_url: str = "/",
        use_ordered_dirty_set: bool = False,
    ): ...

    # Note about `use_ordered_dirty_set`: It's tempting to make it `True` per
    # default so that the unit tests are deterministic, but there have been
    # plenty of tests in the past that only failed *sometimes*, and without that
    # randomness we wouldn't have found the bug at all.
    def __init__(  # type: ignore
        self,
        app_or_build: rio.App | t.Callable[[], rio.Component] | None = None,
        *,
        app: rio.App | None = None,
        build: t.Callable[[], rio.Component] | None = None,
        app_name: str = "test-app",
        default_attachments: t.Iterable[object] = (),
        running_in_window: bool = False,
        user_settings: JsonDoc = {},
        active_url: str = "/",
        use_ordered_dirty_set: bool = False,
    ):
        if app is None:
            if isinstance(app_or_build, rio.App):
                app = app_or_build
            else:
                if build is None:
                    if app_or_build is not None:
                        build = app_or_build
                    else:
                        build = rio.Spacer

                app = rio.App(
                    build=build,
                    name=app_name,
                    default_attachments=tuple(default_attachments),
                )

        self._app_server = TestingServer(
            app,
            debug_mode=False,
            running_in_window=running_in_window,
        )

        self._user_settings = user_settings
        self._active_url = active_url
        self._use_ordered_dirty_set = use_ordered_dirty_set

        self._session: rio.Session | None = None
        self._transport = MessageRecorderTransport(
            process_sent_message=self._process_sent_message
        )
        self._first_refresh_completed = asyncio.Event()

    def _process_sent_message(self, message: JsonDoc) -> None:
        if "id" in message:
            self._transport.queue_response(
                {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "result": None,
                }
            )

        if message["method"] == "updateComponentStates":
            self._first_refresh_completed.set()

    async def __aenter__(self) -> te.Self:
        url = str(rio.URL("http://unit.test") / self._active_url.lstrip("/"))

        self._session = await self._app_server.create_session(
            initial_message=data_models.InitialClientMessage.from_defaults(
                url=url,
                user_settings=self._user_settings,
            ),
            transport=self._transport,
            client_ip="localhost",
            client_port=12345,
            http_headers=starlette.datastructures.Headers(),
        )

        if self._use_ordered_dirty_set:
            self._session._dirty_components = ordered_set.OrderedSet(
                self._session._dirty_components
            )  # type: ignore

        await self._first_refresh_completed.wait()

        return self

    async def __aexit__(self, *_) -> None:
        if self._session is not None:
            await self._session._close(close_remote_session=False)

    async def _simulate_interrupted_connection(self) -> None:
        assert self._session is not None

        self._transport.queue_response(TransportInterrupted)

        while self._session._is_connected_event.is_set():
            await asyncio.sleep(0.05)

    async def _simulate_reconnect(self) -> None:
        assert self._session is not None

        # If currently connected, disconnect first
        if self._session._is_connected_event.is_set():
            await self._simulate_interrupted_connection()

        self._transport = MessageRecorderTransport(
            process_sent_message=self._process_sent_message
        )
        self._session._rio_transport = self._transport

    @property
    def _outgoing_messages(self) -> list[JsonDoc]:
        return self._transport.sent_messages

    @property
    def _dirty_components(self) -> set[rio.Component]:
        return set(self.session._dirty_components)

    @property
    def _last_updated_components(self) -> set[rio.Component]:
        return set(self._last_component_state_changes)

    @property
    def _last_component_state_changes(
        self,
    ) -> t.Mapping[rio.Component, t.Mapping[str, object]]:
        for message in reversed(self._transport.sent_messages):
            if message["method"] == "updateComponentStates":
                delta_states: dict = message["params"]["delta_states"]  # type: ignore
                return {
                    self.session._weak_components_by_id[
                        int(component_id)
                    ]: delta
                    for component_id, delta in delta_states.items()
                    if int(component_id)
                    != self.session._high_level_root_component._id_
                }

        return {}

    def _get_build_output(
        self,
        component: rio.Component,
        type_: type[C] | None = None,
    ) -> C:
        result = component._build_data_.build_result  # type: ignore

        if type_ is not None:
            assert type(result) is type_, (
                f"Expected {type_}, got {type(result)}"
            )

        return result  # type: ignore

    @property
    def session(self) -> rio.Session:
        assert self._session is not None

        return self._session

    @property
    def crashed_build_functions(self) -> t.Mapping[t.Callable, str]:
        return self.session._crashed_build_functions

    @property
    def root_component(self) -> rio.Component:
        return self.session._get_user_root_component()

    def get_components(self, component_type: type[C]) -> t.Iterator[C]:
        root_component = self.root_component

        for component in root_component._iter_component_tree_():
            if type(component) is component_type:
                yield component  # type: ignore

    def get_component(self, component_type: type[C]) -> C:
        try:
            return next(self.get_components(component_type))
        except StopIteration:
            raise AssertionError(f"No component of type {component_type} found")

    async def refresh(self) -> None:
        await self.session._refresh()
