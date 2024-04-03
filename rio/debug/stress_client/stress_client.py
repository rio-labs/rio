from __future__ import annotations

from typing import *  # type: ignore

from uniserde import JsonDoc


class StressClient:
    """
    This is a fake client for Rio apps, which allows to send requests to the
    server to find errors and test the server under load.
    """

    def __init__(
        self,
        send_message: Callable[[JsonDoc], Awaitable[None]],
        receive_message: Callable[[], Awaitable[JsonDoc]],
    ) -> None:
        # Used to talk to the Rio server
        self.send_message = send_message
        self.receive_message = receive_message

        # True, if the

    async def serve(self) -> None:
        raise NotImplementedError
