from __future__ import annotations

import dataclasses
import logging
import typing as t

import imy.docstrings
from uniserde import JsonDoc

import rio

from .. import deprecations, utils
from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = [
    "FilePickEvent",
    "FilePickerArea",
]


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class FilePickEvent:
    """
    Holds information regarding a file upload event.

    This is a simple dataclass that stores useful information for when the user
    picks a file using a `FilePickerArea`. You'll typically receive this as
    argument in `on_pick_file` events.

    ## Attributes

    `file`: Handle to the uploaded file.
    """

    file: rio.FileInfo


@t.final
@deprecations.component_kwarg_renamed(
    since="0.10.9",
    old_name="on_choose_file",
    new_name="on_pick_file",
)
class FilePickerArea(FundamentalComponent):
    """
    Drag & Drop are for files

    The `FilePickerArea` component allows the user to upload files either by
    dragging and dropping them onto the component, or optionally using a regular
    file browser. Whenever a file has been uploaded, the `on_pick_file` event
    is triggered, allowing you to run code.

    ## Attributes

    `file_types`: A list of file extensions which the user is allowed
        to select. Defaults to `None`, which means that the user may select any
        file. Values can be passed as file extensions, ('pdf', '.pdf', '*.pdf'
        are all accepted) or MIME types (e.g. 'application/pdf').

        Note that there is no way for Rio to enforce the file type. Users will
        always be able to upload arbitrary files, e.g. by renaming them. Treat
        this as a hint to the user, and so the file browser may filter files,
        but not as a security measure.

    `multiple`: Whether the user is allowed to pick multiple files at once. If
        `False`, a maximum of one file can be picked at a time.

    `files`: A list of files that has been picked by the user. These will be
        displayed to them and they'll also have the ability to remove them,
        triggering the `on_remove_file` event.

    `on_pick_file`: Triggered when the user picks a file, either by dragging
        and dropping it onto the component, or by selecting it in the file
        browser. The event data contains `FileInfo` object, which contains
        information about the uploaded file.

    `on_remove_file`: Triggered when the user removes a file from the list of
        picked files. The event data contains `FileInfo` object, which contains
        information about the removed file.


    ## Metadata

    `experimental`: True
    """

    file_types: list[str] | None = None

    multiple: bool = False

    files: list[rio.FileInfo] = []

    on_pick_file: rio.EventHandler[FilePickEvent] = None
    on_remove_file: rio.EventHandler[FilePickEvent] = None

    # Hide internal fields from the type checker
    if not t.TYPE_CHECKING:
        # At most one of these is set, the other `None`. If both are `None`, the
        # component will display a default message.
        child_text: str | None = dataclasses.field(default=None, init=False)
        child_component: rio.Component | None = dataclasses.field(
            default=None, init=False
        )

    # The serializer can't handle Union types. Override the constructor, so it
    # splits the content into two values
    def __init__(
        self,
        content: str | rio.Component | None = None,
        *,
        file_types: list[str] | None = None,
        multiple: bool = False,
        files: list[rio.FileInfo] | None = None,
        on_pick_file: rio.EventHandler[FilePickEvent] = None,
        on_remove_file: rio.EventHandler[FilePickEvent] = None,
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
    ) -> None:
        """
        ## Parameters

        `content`: What to display to the user. By default, a simple text
            message is shown. If you pass in a string, the component will
            display that text instead. You may also pass in a component, which
            will be displayed instead of the default look.
        """
        super().__init__(
            key=key,
            margin=margin,
            margin_x=margin_x,
            margin_y=margin_y,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
            align_x=align_x,
            align_y=align_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
            accessibility_role=accessibility_role,
        )

        if content is None:
            self.child_text = None
            self.child_component = None
        elif isinstance(content, str):
            self.child_text = content
            self.child_component = None
        else:
            self.child_text = None
            self.child_component = content

        self.file_types = file_types
        self.multiple = multiple

        if files is None:
            files = []
        self.files = files

        self.on_pick_file = on_pick_file
        self.on_remove_file = on_remove_file

        self._properties_set_by_creator_.update(
            ("child_text", "child_component")
        )

    def _custom_serialize_(self) -> JsonDoc:
        result: JsonDoc = {
            "files": [
                {
                    # Send the ID as string, because JavaScript numbers have a
                    # much more limited range than Python's
                    "id": str(id(file)),
                    "name": file.name,
                }
                for file in sorted(
                    self.files,
                    key=lambda file: file.name.lower(),
                )
            ],
        }

        if self.file_types is not None:
            result["file_types"] = list(
                {
                    utils.normalize_file_extension(file_type)
                    for file_type in self.file_types
                }
            )

        return result

    async def _on_file_upload_(self, files: list[rio.FileInfo]) -> None:
        """
        Special method that's called by Rio when a file is uploaded directly to
        a component, rather than prior registration. Hand off any received
        files.
        """
        await self._update_files(
            add_files=files,
            remove_file_id=None,
        )

    async def _on_message_(self, msg: t.Any) -> None:
        msg_type = msg.get("type", "<invalid>")

        # When running in a window, having the browser upload a file is rather
        # silly. Instead, it will send a message to the component, which will in
        # turn use the session's file picking abilities.
        if msg_type == "pickFile":
            try:
                # The type checker doesn't quite grok the very advanced concept of
                # booleans. Help it out.
                if self.multiple:
                    picked_files = await self.session.pick_file(
                        file_types=self.file_types,
                        multiple=True,
                    )
                else:
                    picked_files = [
                        await self.session.pick_file(
                            file_types=self.file_types,
                            multiple=False,
                        )
                    ]

            # If no files were selected that's fine. No need to spam stdout.
            except rio.NoFileSelectedError:
                return

            # Update the state & call event handlers
            await self._update_files(
                add_files=picked_files,
                remove_file_id=None,
            )

        # Allow the user to unpick files
        elif msg_type == "removeFile":
            await self._update_files(
                add_files=[],
                remove_file_id=msg.get("fileId"),
            )

        # Wah?!
        else:
            logging.error(
                f"Received invalid message from the frontend. This is either a bug, or somebody is crafting invalid messages on purpose. Received message was: {msg}"
            )

    async def _update_files(
        self,
        *,
        add_files: list[rio.FileInfo],
        remove_file_id: str | None,
    ) -> None:
        """
        Adds a file to the list of picked files, managing state and triggering
        events as needed.
        """
        actually_added_files: list[rio.FileInfo] = []
        actually_removed_files: list[rio.FileInfo] = []

        # Add any new files
        if self.multiple:
            actually_added_files.extend(add_files)
            self.files.extend(add_files)
        elif add_files:
            actually_added_files.append(add_files[0])
            actually_removed_files.extend(self.files)
            self.files.clear()
            self.files.append(add_files[0])

        # Remove any files
        if remove_file_id is not None:
            for ii, file in enumerate(self.files):
                if str(id(file)) == remove_file_id:
                    actually_removed_files.append(self.files.pop(ii))
                    break

        # Call event handlers
        #
        # TODO: Should these be called simultaneously?
        for file in actually_added_files:
            event_data = FilePickEvent(file)
            await self.call_event_handler(
                self.on_pick_file,
                event_data,
            )

        for file in actually_removed_files:
            event_data = FilePickEvent(file)
            await self.call_event_handler(
                self.on_remove_file,
                event_data,
            )

        # If files were added or removed, reassign the `files` property so that
        # everyone depending on it gets rebuilt
        if actually_added_files or actually_removed_files:
            self.files = self.files


FilePickerArea._unique_id_ = "FilePickerArea-builtin"
