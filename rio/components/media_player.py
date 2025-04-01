from __future__ import annotations

import pathlib
import typing as t

from uniserde import JsonDoc

import rio

from .. import assets, color, fills
from ..utils import EventHandler
from .component import AccessibilityRole, Key
from .keyboard_focusable_components import KeyboardFocusableFundamentalComponent

__all__ = ["MediaPlayer"]


@t.final
class MediaPlayer(KeyboardFocusableFundamentalComponent):
    """
    Plays audio and video files.

    `MediaPlayer` plays back audio and video files. It can play both local files
    and URLs.

    Note that the `MediaPlayer` component doesn't reserve any specific amount of
    space for itself, it simply makes do with the space it is given by its
    parent component.


    ## Attributes

    `media`: The media to play. This can be a file path, URL, or bytes.

    `media_type`: The mime type of the media file. May help the browser play the
        file correctly.

    `loop`: Whether to automatically restart from the beginning when the
        playback ends.

    `autoplay`: Whether to start playing the media automatically, without
        requiring the user to press "Play".

    `controls`: Whether to display controls like a Play/Pause button, volume
        slider, etc.

    `muted`: Whether to mute the audio.

    `volume`: The volume to play the audio at. 1.0 is the native volume;
        larger numbers increase the volume, smaller numbers decrease it.

    `background`: The background fill. This is visible when playing audio or
        when the video doesn't use up all the available space.

    `on_playback_end`: Triggers when the played file reaches the end. This will
        be called even if the `loop` attribute is set to `True`.

    `on_error`: Triggered should any error with the playback occur, for example
        because the file format isn't supported.


    ## Examples

    A minimal example of a `MediaPlayer` playing a media file from the internet:

    ```python
    rio.MediaPlayer(rio.URL("https://example.com/example_video.mp4"))
    ```

    You can also display videos from a path. Note that Rio uses modern python
    `pathlib.Path` objects rather than plain strings:

    ```python
    from pathlib import Path

    rio.MediaPlayer(Path("example_video.mp4"))
    ```

    You can access the `App`'s assets directory using the `assets` property. This
    will return a `pathlib.Path` object pointing to the assets directory:

    ```python
    rio.MediaPlayer(self.session.assets / "example_video.mp4")
    ```
    """

    media: pathlib.Path | rio.URL | bytes
    media_type: str | None
    loop: bool
    autoplay: bool
    controls: bool
    muted: bool
    volume: float
    background: fills._FillLike
    on_playback_end: EventHandler[[]]
    on_error: EventHandler[[]]

    def __init__(
        self,
        media: pathlib.Path | rio.URL | bytes,
        *,
        media_type: str | None = None,
        loop: bool = False,
        autoplay: bool = False,
        controls: bool = True,
        muted: bool = False,
        volume: float = 1.0,
        background: fills._FillLike = color.Color.BLACK,
        on_playback_end: EventHandler[[]] = None,
        on_error: EventHandler[[]] = None,
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
    ):
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

        self.media = media
        self.media_type = media_type
        self.loop = loop
        self.autoplay = autoplay
        self.controls = controls
        self.muted = muted
        self.volume = volume
        self.background = background
        self.on_playback_end = on_playback_end
        self.on_error = on_error

    def _custom_serialize_(self) -> JsonDoc:
        media_asset = assets.Asset.new(self.media, self.media_type)
        return {
            "mediaUrl": media_asset._serialize(self.session),
            "reportError": self.on_error is not None,
            "reportPlaybackEnd": self.on_playback_end is not None,
        }

    def _validate_delta_state_from_frontend(self, delta_state: JsonDoc) -> None:
        if not set(delta_state) <= {"muted", "volume"}:
            raise AssertionError(
                f"Frontend tried to change `{type(self).__name__}` state: {delta_state}"
            )

    async def _on_message_(self, message: JsonDoc) -> None:  # type: ignore
        if message["type"] == "playbackEnd":
            await self.call_event_handler(self.on_playback_end)
        elif message["type"] == "error":
            await self.call_event_handler(self.on_error)
        else:
            await super()._on_message_(message)


MediaPlayer._unique_id_ = "MediaPlayer-builtin"
