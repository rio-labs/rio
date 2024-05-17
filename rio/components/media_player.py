from __future__ import annotations

import pathlib
from typing import Literal, final

from uniserde import JsonDoc

import rio

from .. import assets, color
from ..utils import EventHandler
from .fundamental_component import KeyboardFocusableFundamentalComponent

__all__ = ["MediaPlayer"]


@final
class MediaPlayer(KeyboardFocusableFundamentalComponent):
    """
    Plays audio and video.

    `MediaPlayer` plays back audio and video files. It can play local files and
    URLs.

    Note that the `MediaPlayer` component doesn't reserve any space for itself,
    it simply makes do with the space it is given by its parent component.


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

    `on_playback_end`: An event handler to call when the media finishes
        playing.

    `on_error`: An event handler to call when an error occurs, for example if
        the file format isn't supported.


    ## Examples

    A minimal example of a `MediaPlayer` playing a media file from the internet:

    ```python
    rio.MediaPlayer(rio.URL("https://example.com/example_video.mp4"))
    ```

    You can use a local file as well:

    ```python
    from pathlib import Path

    rio.MediaPlayer(Path("example_video.mp4"))
    ```
    """

    media: pathlib.Path | rio.URL | bytes
    media_type: str | None
    loop: bool
    autoplay: bool
    controls: bool
    muted: bool
    volume: float
    background: rio.Fill
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
        background: rio.FillLike = color.Color.TRANSPARENT,
        on_playback_end: EventHandler[[]] = None,
        on_error: EventHandler[[]] = None,
        key: str | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        width: float | Literal["natural", "grow"] = "natural",
        height: float | Literal["natural", "grow"] = "natural",
        align_x: float | None = None,
        align_y: float | None = None,
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
            width=width,
            height=height,
            align_x=align_x,
            align_y=align_y,
        )

        self.media = media
        self.media_type = media_type
        self.loop = loop
        self.autoplay = autoplay
        self.controls = controls
        self.muted = muted
        self.volume = volume
        self.background = rio.Fill._try_from(background)
        self.on_playback_end = on_playback_end
        self.on_error = on_error

    def _custom_serialize(self) -> JsonDoc:
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

    async def _on_message(self, message: JsonDoc) -> None:  # type: ignore
        if message["type"] == "playbackEnd":
            await self.call_event_handler(self.on_playback_end)
        elif message["type"] == "error":
            await self.call_event_handler(self.on_error)
        else:
            await super()._on_message(message)


MediaPlayer._unique_id = "MediaPlayer-builtin"
