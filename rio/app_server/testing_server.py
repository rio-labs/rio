from __future__ import annotations

import typing as t

import rio

from .. import assets, utils
from .abstract_app_server import AbstractAppServer

__all__ = ["TestingServer"]


class TestingServer(AbstractAppServer):
    def __init__(
        self,
        app: rio.App,
        *,
        running_in_window: bool = False,
        debug_mode: bool = False,
        base_url: rio.URL | None = None,
    ) -> None:
        super().__init__(
            app,
            running_in_window=running_in_window,
            debug_mode=debug_mode,
            base_url=base_url,
        )

    def weakly_host_asset(self, asset: assets.HostedAsset) -> rio.URL:
        # This method is called for font files, even in a test session, so it
        # actually needs to be implemented.
        return rio.URL(asset.secret_id)

    def external_url_for_user_asset(
        self, relative_asset_path: assets.Path
    ) -> rio.URL:
        raise NotImplementedError

    def url_for_cookies(self, cookies: t.Mapping[str, str]) -> str:
        raise NotImplementedError

    async def pick_file(
        self,
        session: rio.Session,
        *,
        file_types: list[str] | None = None,
        multiple: bool = False,
    ) -> utils.FileInfo | list[utils.FileInfo]:
        raise NotImplementedError
