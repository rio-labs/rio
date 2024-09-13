from __future__ import annotations

from dataclasses import KW_ONLY
from typing import *  # type: ignore

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "UploadArea",
]


@final
class UploadArea(FundamentalComponent):
    _: KW_ONLY

    async def _on_file_upload(self, files: list[rio.FileInfo]) -> None:
        print(f"Files uploaded: {files}")


UploadArea._unique_id_ = "UploadArea-builtin"
