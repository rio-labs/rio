from __future__ import annotations

import typing as t
from dataclasses import KW_ONLY, dataclass

from uniserde import JsonDoc

import rio
import rio.docs

from .. import utils
from .fundamental_component import FundamentalComponent

__all__ = [
    "FilePickEvent",
    "FilePickerArea",
]


@t.final
@rio.docs.mark_constructor_as_private
@dataclass
class FilePickEvent:
    """
    Holds information regarding a file upload event.

    This is a simple dataclass that stores useful information for when the user
    chooses a file using a `FilePickerArea`. You'll typically receive this as
    argument in `on_choose_file` events.

    ## Attributes

    `file`: Handle to the uploaded file.
    """

    file: rio.FileInfo


@t.final
class FilePickerArea(FundamentalComponent):
    """
    Drag & Drop are for files

    The `FilePickerArea` component allows the user to upload files either by
    dragging and dropping them onto the component, or optionally using a regular
    file browser. Whenever a file has been uploaded, the `on_file_upload` event
    is triggered, allowing you to run code.

    ## Attributes

    `content`: A custom text to display to the user. If not provided, the
        component will display a default message.

    `file_types`: A list of file extensions which the user is allowed
        to select. Defaults to `None`, which means that the user may select any
        file. Values can be passed as file extensions, ('pdf', '.pdf', '*.pdf'
        are all accepted) or MIME types (e.g. 'application/pdf').

        Note that there is no way for Rio to enforce the file type. Users will
        always be able to upload arbitrary files, e.g. by renaming them. Treat
        this as a hint to the user, and so the file browser may filter files,
        but not as a security measure.

    `on_choose_file`: Triggered when the user uploads a file, either by dragging
        and dropping it onto the component, or by selecting it in the file
        browser. The event handler receives a `FileInfo` object, which contains
        information about the uploaded file.


    ## Metadata

    `experimental`: True
    """

    _: KW_ONLY
    content: str | None = None
    file_types: list[str] | None = None
    on_choose_file: rio.EventHandler[FilePickEvent] = None

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
            event_data = FilePickEvent(file)

            await self.call_event_handler(
                self.on_choose_file,
                event_data,
            )


FilePickerArea._unique_id_ = "FilePickerArea-builtin"
