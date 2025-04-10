import asyncio

import starlette.datastructures
from uniserde import JsonDoc

import rio
from rio.app_server.abstract_app_server import AbstractAppServer

from .. import data_models
from ..app_server import TestingServer
from ..transports import MessageRecorderTransport, TransportInterrupted
from .base_client import BaseClient

__all__ = ["DummyClient"]


class DummyClient(BaseClient):
    def __post_init__(self) -> None:
        self.__app_server = TestingServer(
            self._app,
            debug_mode=self._debug_mode,
            running_in_window=self._running_in_window,
        )

    def _process_sent_message(self, message: JsonDoc) -> None:
        super()._process_sent_message(message)

        if "id" in message:
            self._recorder_transport.queue_response(
                {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "result": None,
                }
            )

    async def _get_app_server(self) -> AbstractAppServer:
        return self.__app_server

    async def _create_session(self) -> rio.Session:
        url = str(rio.URL("http://unit.test") / self._active_url.lstrip("/"))

        return await self.__app_server.create_session(
            initial_message=data_models.InitialClientMessage.from_defaults(
                url=url,
                user_settings=self._user_settings,
            ),
            transport=self._recorder_transport,
            client_ip="localhost",
            client_port=12345,
            http_headers=starlette.datastructures.Headers(),
        )

    async def _simulate_interrupted_connection(self) -> None:
        assert self._session is not None

        self._recorder_transport.queue_response(TransportInterrupted)

        while self._session._is_connected_event.is_set():
            await asyncio.sleep(0.05)

    async def _simulate_reconnect(self) -> None:
        assert self._session is not None

        # If currently connected, disconnect first
        if self._session._is_connected_event.is_set():
            await self._simulate_interrupted_connection()

        self._recorder_transport = MessageRecorderTransport(
            process_sent_message=self._process_sent_message
        )
        await self._session._replace_rio_transport(self._recorder_transport)
