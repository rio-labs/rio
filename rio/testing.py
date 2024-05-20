import asyncio
import json
import types
from collections.abc import Callable, Iterable, Iterator, Mapping
from typing_extensions import Any, Self, TypeVar, overload

import ordered_set
from uniserde import Jsonable, JsonDoc

import rio
from rio.app_server import AppServer
from rio.components.root_components import (
    FundamentalRootComponent,
    HighLevelRootComponent,
)


__all__ = ["TestClient"]


T = TypeVar("T")
C = TypeVar("C", bound=rio.Component)


class TestClient:
    @overload
    def __init__(
        self,
        app: rio.App,
        *,
        running_in_window: bool = False,
        user_settings: JsonDoc = {},
        active_url: str = "/",
        use_ordered_dirty_set: bool = False,
    ): ...

    @overload
    def __init__(
        self,
        build: Callable[[], rio.Component] = rio.Spacer,
        *,
        app_name: str = "mock-app",
        default_attachments: Iterable[object] = (),
        running_in_window: bool = False,
        user_settings: JsonDoc = {},
        active_url: str = "/",
        use_ordered_dirty_set: bool = False,
    ): ...

    def __init__(  # type: ignore
        self,
        app_or_build: rio.App | Callable[[], rio.Component] | None = None,
        *,
        app: rio.App | None = None,
        build: Callable[[], rio.Component] | None = None,
        app_name: str = "mock-app",
        default_attachments: Iterable[object] = (),
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

        self._app_server = AppServer(
            app,
            debug_mode=False,
            running_in_window=running_in_window,
            validator_factory=None,
            internal_on_app_start=None,
        )

        self._use_ordered_dirty_set = use_ordered_dirty_set

        self._session: rio.Session | None = None
        self._server_task: asyncio.Task | None = None
        self._outgoing_messages = list[JsonDoc]()
        self._responses = asyncio.Queue[JsonDoc]()
        self._responses.put_nowait(
            {
                "websiteUrl": "https://unit.test" + active_url,
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
        self._first_refresh_completed = asyncio.Event()

    async def _send_message(self, message_text: str) -> None:
        message = json.loads(message_text)

        self._outgoing_messages.append(message)

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

    async def __aenter__(self) -> Self:
        # Emulate the process of creating a session as closely as possible
        fake_request: Any = types.SimpleNamespace(
            url="https://unit.test",
            base_url="https://unit.test",
            headers={"accept": "text/html"},
            client=types.SimpleNamespace(host="localhost", port="12345"),
        )
        await self._app_server._serve_index(fake_request, "")

        [[session_token, session]] = (
            self._app_server._active_session_tokens.items()
        )
        self._session = session

        if self._use_ordered_dirty_set:
            session._dirty_components = ordered_set.OrderedSet(
                session._dirty_components
            )  # type: ignore

        fake_websocket: Any = types.SimpleNamespace(
            client="1.2.3.4",
            accept=lambda: _make_awaitable(),
            send_text=self._send_message,
            receive_json=self._receive_message,
        )

        test_task = asyncio.current_task()
        assert test_task is not None

        async def serve_websocket():
            try:
                await self._app_server._serve_websocket(
                    fake_websocket, session_token
                )
            except asyncio.CancelledError:
                pass
            except Exception as error:
                test_task.cancel(
                    f"Exception in AppServer._serve_websocket: {error}"
                )
            else:
                test_task.cancel(
                    "AppServer._serve_websocket exited unexpectedly. An"
                    " exception must have occurred in the `init_coro`."
                )

        self._server_task = asyncio.create_task(serve_websocket())

        await self._first_refresh_completed.wait()
        return self

    async def __aexit__(self, *_) -> None:
        if self._server_task is not None:
            self._server_task.cancel()

    @property
    def _dirty_components(self) -> set[rio.Component]:
        return set(self.session._dirty_components)

    @property
    def _last_updated_components(self) -> set[rio.Component]:
        return set(self._last_component_state_changes)

    @property
    def _last_component_state_changes(
        self,
    ) -> Mapping[rio.Component, Mapping[str, object]]:
        for message in reversed(self._outgoing_messages):
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

    def _get_build_output(
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

    @property
    def session(self) -> rio.Session:
        assert self._session is not None

        return self._session

    @property
    def crashed_build_functions(self) -> Mapping[Callable, str]:
        return self.session._crashed_build_functions

    @property
    def root_component(self) -> rio.Component:
        high_level_root = self.session._root_component
        assert isinstance(
            high_level_root, HighLevelRootComponent
        ), high_level_root

        low_level_root = self.session._weak_component_data_by_component[
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
        root_component = self.root_component

        for component in root_component._iter_component_tree():
            if type(component) is component_type:
                yield component  # type: ignore

    def get_component(self, component_type: type[C]) -> C:
        try:
            return next(self.get_components(component_type))
        except StopIteration:
            raise AssertionError(f"No component of type {component_type} found")

    async def refresh(self) -> None:
        await self.session._refresh()


async def _make_awaitable(value: T = None) -> T:
    return value
