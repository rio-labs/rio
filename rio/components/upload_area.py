from __future__ import annotations

from dataclasses import KW_ONLY
from typing import *  # type: ignore

from uniserde import JsonDoc

import rio

from .. import utils
from .fundamental_component import FundamentalComponent

__all__ = [
    "UploadArea",
]


@final
class UploadArea(FundamentalComponent):
    content: str | None = None
    _: KW_ONLY
    file_types: list[str] | None = None
    on_file_upload: rio.EventHandler[rio.FileInfo] = None

    def _custom_serialize_(self) -> JsonDoc:
        if self.file_types is None:
            return {}

        return {
            "file_types": list(
                {
                    utils.normalize_file_type(file_type)
                    for file_type in self.file_types
                }
            )
        }

    async def _on_file_upload_(self, files: list[rio.FileInfo]) -> None:
        for file in files:
            # TODO: Should these be called simultaneously?
            await self.call_event_handler(self.on_file_upload, file)


UploadArea._unique_id_ = "UploadArea-builtin"
