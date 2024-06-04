import asyncio
import json
from collections.abc import Callable

from uniserde import JsonDoc

from .abstract_transport import *

__all__ = ["MessageRecorderTransport"]


class MessageRecorderTransport(AbstractTransport):
    def __init__(
        self, *, process_sent_message: Callable[[JsonDoc], None] | None = None
    ):
        super().__init__()

        self.process_sent_message = process_sent_message

        self.sent_messages = list[JsonDoc]()
        self._responses = asyncio.Queue[JsonDoc | None]()

    async def send(self, msg: str) -> None:
        parsed_msg = json.loads(msg)
        self.sent_messages.append(parsed_msg)

        if self.process_sent_message is not None:
            self.process_sent_message(parsed_msg)

    async def receive(self) -> JsonDoc:
        response = await self._responses.get()

        if response is None:
            raise TransportClosedIntentionally

        return response

    def close(self) -> None:
        self._responses.put_nowait(None)
        self.closed.set()

    def queue_response(self, response: JsonDoc) -> None:
        self._responses.put_nowait(response)
