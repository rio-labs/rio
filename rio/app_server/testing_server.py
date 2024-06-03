from __future__ import annotations

from typing import *

import rio

from .. import assets, utils
from .abstract_app_server import AbstractAppServer

__all__ = ["TestingServer"]


class TestingServer(AbstractAppServer):
    def weakly_host_asset(self, asset: assets.HostedAsset) -> str:
        # This method is called for font files, even in a test session, so it
        # actually needs to be implemented.
        return asset.secret_id

    def url_for_user_asset(self, relative_asset_path: assets.Path) -> rio.URL:
        raise NotImplementedError

    async def file_chooser(
        self,
        session: rio.Session,
        *,
        file_extensions: Iterable[str] | None = None,
        multiple: bool = False,
    ) -> utils.FileInfo | tuple[utils.FileInfo, ...]:
        raise NotImplementedError
