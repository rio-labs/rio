from __future__ import annotations

from typing import *

import rio

from .. import assets, utils
from .abstract_app_server import AbstractAppServer

__all__ = ["TestingServer"]


class TestingServer(AbstractAppServer):
    def weakly_host_asset(self, asset: assets.HostedAsset) -> str:
        raise NotImplementedError

    async def file_chooser(
        self,
        session: rio.Session,
        *,
        file_extensions: Iterable[str] | None = None,
        multiple: bool = False,
    ) -> utils.FileInfo | tuple[utils.FileInfo, ...]:
        raise NotImplementedError
