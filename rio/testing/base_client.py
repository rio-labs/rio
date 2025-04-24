import abc
import asyncio
import typing as t

import typing_extensions as te
from uniserde import JsonDoc

import rio
import rio.app_server

from ..components.component import Key
from ..transports import MessageRecorderTransport

__all__ = ["BaseClient"]


T = t.TypeVar("T")
C = t.TypeVar("C", bound=rio.Component)


class BaseClient(abc.ABC):
    @t.overload
    def __init__(
        self,
        app: rio.App,
        *,
        running_in_window: bool = False,
        user_settings: JsonDoc = {},
        active_url: str = "/",
        debug_mode: bool = False,
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
        debug_mode: bool = False,
    ): ...

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
        debug_mode: bool = False,
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

        self._app = app
        self._user_settings = user_settings
        self._active_url = active_url
        self._running_in_window = running_in_window
        self._debug_mode = debug_mode

        self._recorder_transport = MessageRecorderTransport(
            process_sent_message=self._process_sent_message
        )
        self._refresh_completed = asyncio.Event()

        self._app_server: rio.app_server.AbstractAppServer | None = None
        self._session: rio.Session | None = None

        # Overriding this function is miserable because of the overloads and
        # myriad of parameters, so we'll provide a __post_init__ for convenience
        self.__post_init__()

    def __post_init__(self) -> None:
        pass

    @abc.abstractmethod
    async def _get_app_server(self) -> rio.app_server.AbstractAppServer:
        raise NotImplementedError

    @abc.abstractmethod
    async def _create_session(self) -> rio.Session:
        raise NotImplementedError

    def _process_sent_message(self, message: JsonDoc) -> None:
        if message["method"] == "updateComponentStates":
            self._refresh_completed.set()

    async def __aenter__(self) -> te.Self:
        self._app_server = await self._get_app_server()
        self._app_server.app = self._app
        self._app_server.debug_mode = self._debug_mode

        self._session = await self._create_session()

        await self._refresh_completed.wait()

        return self

    async def __aexit__(self, *_) -> None:
        if self._session is not None:
            await self._session._close(close_remote_session=False)

    @property
    def _received_messages(self) -> list[JsonDoc]:
        # From a "client" perspective they are "received" messages, but from a
        # "transport" perspective they are "sent" messages
        return self._recorder_transport.sent_messages

    @property
    def _dirty_components(self) -> set[rio.Component]:
        return self.session._collect_components_to_build()

    @property
    def _last_updated_components(self) -> set[rio.Component]:
        return set(self._last_component_state_changes)

    @property
    def _last_component_state_changes(
        self,
    ) -> t.Mapping[rio.Component, t.Mapping[str, object]]:
        for message in reversed(self._received_messages):
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

    def get_components(
        self,
        component_type: type[C] = rio.Component,
        key: Key | None = None,
    ) -> t.Iterator[C]:
        roots = [self.root_component]

        for root_component in roots:
            for component in root_component._iter_component_tree_():
                if isinstance(component, component_type) and (
                    key is None or key == component.key
                ):
                    yield component

                roots.extend(
                    dialog._root_component
                    for dialog in component._owned_dialogs_.values()
                )

    def get_component(
        self,
        component_type: type[C] = rio.Component,
        key: Key | None = None,
    ) -> C:
        try:
            return next(self.get_components(component_type, key=key))
        except StopIteration:
            # Try to figure out why it doesn't exist. Maybe the parent's `build`
            # function crashed.
            if not self.crashed_build_functions:
                raise ValueError(f"No component of type {component_type} found")

            crashes = "\n".join(
                f"- {error}" for error in self.crashed_build_functions.values()
            )
            raise ValueError(
                f"No component of type {component_type} found. Perhaps its parent's `build` function crashed? Here are the errors:\n{crashes}"
            )

    async def wait_for_refresh(self) -> None:
        self._refresh_completed.clear()
        await self._refresh_completed.wait()
