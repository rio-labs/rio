import asyncio
import functools
import inspect
from typing import TypeVar

import starlette.datastructures
import fastapi
import pytz
from uniserde import Jsonable

import rio.global_state
from rio.app_server import AppServer
from rio.components.root_components import (
    HighLevelRootComponent,
)


__all__ = ["enable_component_instantiation"]


T = TypeVar("T")
C = TypeVar("C", bound=rio.Component)


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
            internal_on_app_start=None,
        )
        websocket: fastapi.WebSocket = None  # type: ignore
        session = rio.Session(
            app_server_=app_server,
            session_token="<a fake session token>",
            send_message=_fake_send_message,
            receive_message=_fake_receive_message,
            websocket=websocket,
            client_ip="localhost",
            client_port=12345,
            http_headers=starlette.datastructures.Headers(),
            timezone=pytz.UTC,
            decimal_separator=".",
            thousands_separator=",",
            window_width=1920,
            window_height=1080,
            base_url=rio.URL("https://unit.test"),
            theme_=rio.Theme.from_colors(),
        )

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
