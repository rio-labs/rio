import asyncio
import contextlib
import functools
import inspect
import json
import types
from collections.abc import (
    AsyncGenerator,
    Callable,
    Container,
    Iterable,
    Iterator,
    Mapping,
)
from typing import Any, TypeVar

import ordered_set
from uniserde import Jsonable, JsonDoc

import rio.global_state
from rio.app_server import AppServer
from rio.components.root_components import (
    FundamentalRootComponent,
    HighLevelRootComponent,
)

T = TypeVar("T")
C = TypeVar("C", bound=rio.Component)


async def _make_awaitable(value: T = None) -> T:
    return value


class MockApp:
    def __init__(
        self,
        session: rio.Session,
        user_settings: JsonDoc = {},
    ) -> None:
        self.session = session
        self.outgoing_messages: list[JsonDoc] = []

        self._first_refresh_completed = asyncio.Event()

        self._responses = asyncio.Queue[JsonDoc]()
        self._responses.put_nowait(
            {
                "websiteUrl": "https://unit.test",
                "preferredLanguages": [],
                "userSettings": user_settings,
                "windowWidth": 1920,
                "windowHeight": 1080,
                "timezone": "America/New_York",
                "decimalSeparator": ".",
                "thousandsSeparator": ",",
                "prefersLightTheme": True,
            }
        )

    async def _send_message(self, message_text: str) -> None:
        message = json.loads(message_text)

        self.outgoing_messages.append(message)

        if "id" in message:
            self._responses.put_nowait(
                {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "result": None,
                }
            )

        if message["method"] == "updateComponentStates":
            self._first_refresh_completed.set()

    async def _receive_message(self) -> Jsonable:
        return await self._responses.get()

    @property
    def dirty_components(self) -> Container[rio.Component]:
        return set(self.session._dirty_components)

    @property
    def last_updated_components(self) -> set[rio.Component]:
        return set(self.last_component_state_changes)

    @property
    def last_component_state_changes(
        self,
    ) -> Mapping[rio.Component, Mapping[str, object]]:
        for message in reversed(self.outgoing_messages):
            if message["method"] == "updateComponentStates":
                delta_states: dict = message["params"]["deltaStates"]  # type: ignore
                return {
                    self.session._weak_components_by_id[
                        int(component_id)
                    ]: delta
                    for component_id, delta in delta_states.items()
                    if int(component_id) != self.session._root_component._id
                }

        return {}

    def get_root_component(self) -> rio.Component:
        sess = self.session

        high_level_root = sess._root_component
        assert isinstance(
            high_level_root, HighLevelRootComponent
        ), high_level_root

        low_level_root = sess._weak_component_data_by_component[
            high_level_root
        ].build_result
        assert isinstance(
            low_level_root, FundamentalRootComponent
        ), low_level_root

        scroll_container = low_level_root.content
        assert isinstance(
            scroll_container, rio.ScrollContainer
        ), scroll_container

        return scroll_container.content

    def get_components(self, component_type: type[C]) -> Iterator[C]:
        root_component = self.get_root_component()

        for component in root_component._iter_component_tree():
            if type(component) is component_type:
                yield component  # type: ignore

    def get_component(self, component_type: type[C]) -> C:
        try:
            return next(self.get_components(component_type))
        except StopIteration:
            raise AssertionError(f"No component of type {component_type} found")

    def get_build_output(
        self,
        component: rio.Component,
        type_: type[C] | None = None,
    ) -> C:
        result = self.session._weak_component_data_by_component[
            component
        ].build_result

        if type_ is not None:
            assert (
                type(result) is type_
            ), f"Expected {type_}, got {type(result)}"

        return result  # type: ignore

    async def refresh(self) -> None:
        await self.session._refresh()


@contextlib.asynccontextmanager
async def create_mockapp(
    build: Callable[[], rio.Component] = lambda: rio.Text("hi"),
    *,
    app_name: str = "mock-app",
    running_in_window: bool = False,
    user_settings: JsonDoc = {},
    default_attachments: Iterable[object] = (),
    use_ordered_dirty_set: bool = False,
) -> AsyncGenerator[MockApp, None]:
    app = rio.App(
        build=build,
        name=app_name,
        default_attachments=tuple(default_attachments),
    )
    app_server = AppServer(
        app,
        debug_mode=False,
        running_in_window=running_in_window,
        validator_factory=None,
        internal_on_app_start=None,
    )

    # Emulate the process of creating a session as closely as possible
    fake_request: Any = types.SimpleNamespace(
        url="https://unit.test",
        base_url="https://unit.test",
        headers={"accept": "text/html"},
    )
    await app_server._serve_index(fake_request, "")

    [[session_token, session]] = app_server._active_session_tokens.items()

    if use_ordered_dirty_set:
        session._dirty_components = ordered_set.OrderedSet(
            session._dirty_components
        )  # type: ignore

    mock_app = MockApp(session, user_settings=user_settings)

    fake_websocket: Any = types.SimpleNamespace(
        client="1.2.3.4",
        accept=lambda: _make_awaitable(),
        send_text=mock_app._send_message,
        receive_json=mock_app._receive_message,
    )

    test_task = asyncio.current_task()
    assert test_task is not None

    async def serve_websocket():
        try:
            await app_server._serve_websocket(fake_websocket, session_token)
        except asyncio.CancelledError:
            pass
        except Exception as error:
            test_task.cancel(
                f"Exception in AppServer._serve_websocket: {error}"
            )
        else:
            test_task.cancel(
                "AppServer._serve_websocket exited unexpectedly. An exception"
                " must have occurred in the `init_coro`."
            )

    server_task = asyncio.create_task(serve_websocket())

    await mock_app._first_refresh_completed.wait()
    try:
        yield mock_app
    finally:
        server_task.cancel()


def enable_component_instantiation(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        def build():
            result = func(*args, **kwargs)
            assert not inspect.isawaitable(
                result
            ), "The test function must not be async"

            return rio.Text("")

        app = rio.App(build=build)
        app_server = AppServer(
            app_=app,
            debug_mode=False,
            running_in_window=False,
            validator_factory=None,
            internal_on_app_start=None,
        )
        session = rio.Session(
            app_server,
            "<a fake session token>",
        )
        session._decimal_separator = "."
        session._thousands_separator = ","
        session._send_message = _fake_send_message
        session._receive_message = _fake_receive_message

        rio.global_state.currently_building_session = session
        session._root_component = HighLevelRootComponent(
            build, lambda: rio.Text("")
        )

        rio.global_state.currently_building_component = session._root_component
        try:
            session._root_component.build()
        finally:
            rio.global_state.currently_building_component = None
            rio.global_state.currently_building_session = None

    return wrapper


async def _fake_send_message(message: Jsonable) -> None:
    pass


async def _fake_receive_message() -> Jsonable:
    while True:
        await asyncio.sleep(100000)
