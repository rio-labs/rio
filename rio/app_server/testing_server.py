from __future__ import annotations

import rio

from .. import assets, utils
from .abstract_app_server import AbstractAppServer

__all__ = ["TestingServer"]


class TestingServer(AbstractAppServer):
    def weakly_host_asset(self, asset: assets.HostedAsset) -> rio.URL:
        # This method is called for font files, even in a test session, so it
        # actually needs to be implemented.
        return rio.URL(asset.secret_id)

    def external_url_for_user_asset(
        self, relative_asset_path: assets.Path
    ) -> rio.URL:
        raise NotImplementedError

    async def pick_file(
        self,
        session: rio.Session,
        *,
        file_types: list[str] | None = None,
        multiple: bool = False,
    ) -> utils.FileInfo | list[utils.FileInfo]:
        raise NotImplementedError
