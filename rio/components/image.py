from __future__ import annotations

import dataclasses
import typing as t

from uniserde import Jsonable, JsonDoc

from .. import assets
from ..utils import EventHandler, ImageLike
from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = ["Image"]


@t.final
class Image(FundamentalComponent):
    """
    Displays a raster image or SVG.

    `Image` does just what you'd expect: it displays a single image. The image
    can be loaded from a URL or a local file.

    The resolution of the image does not affect the size at which it is
    displayed. The `Image` component is flexible with its space requirements and
    adapts to any space allocated by its parent component.

    Note that unlike most components in Rio, the `Image` component does not have
    a `natural` size, since images can be easily be scaled to fit any space.
    Because of this, `Image` defaults to a width and height of 2. This avoids
    invisible images when you forget to set the size.

    The actual picture content can be scaled to fit the assigned shape in one of
    three ways:

    - `"fit"`: The image is scaled to fit entirely inside the shape, while
      maintaining its aspect ratio. This is the default.
    - `"stretch"`: The image is stretched to fill the shape, distorting it if
      necessary.
    - `"zoom"`: The image is scaled to fill the shape entirely, while maintaining
      its aspect ratio. This may cause the image to overflow the shape.

    The image data may be provided in several ways. If the image is already
    hosted somewhere, you can provide a `rio.URL` for easy access. To display a
    local file use a `pathlib.Path` object. Finally, if you already have the
    image data in memory you can either pass it as a `bytes` object or as a
    `PIL.Image` object.


    ## Attributes

    `image`: The image to display.

    `fill_mode`: How the image should be scaled to fit the shape. If `fit`,
        the image is scaled to fit entirely inside the shape. If `stretch`,
        the image is stretched to fill the shape exactly, possibly
        distorting it in the process. If `zoom`, the image is scaled to fill
        the shape entirely, possibly overflowing.

    `on_error`: A function, triggered if the image fails to load.

    `corner_radius`: How round to make the corners of the image. If a single
        number is given, all four corners will be rounded equally. If a
        tuple of four numbers is given, they will be interpreted as the
        radii of the top-left, top-right, bottom-right, and bottom-left
        corners, in that order.

    `accessibility_description`: A description of the image, for screen readers.


    ## Examples

    This minimal example will display an image hosted on the web:

    ```python
    rio.Image(
        rio.URL("https://example.com/image.png"),
        min_width=20,
        min_height=20,
    )
    ```

    You can also display images from a path. Note that Rio uses modern python
    `pathlib.Path` objects rather than plain strings. The image will be scaled
    to fit the shape, and the corners will be rounded with a radius of 2:

    ```python
    from pathlib import Path

    rio.Image(
        Path("example_image.png"),
        fill_mode="fit",
        min_width=20,
        min_height=20,
        corner_radius=2,
    )
    ```

    You can access the `App`'s assets directory using the `assets` property. This
    will return a `pathlib.Path` object pointing to the assets directory. The
    image will be scaled to fit the shape, and the corners will be rounded with
    a radius of 2:

    ```python
    rio.Image(
        Path(self.session.assets / "example_image.png"),
        fill_mode="fit",
        min_width=20,
        min_height=20,
        corner_radius=2,
    )
    ```
    """

    image: ImageLike
    _: dataclasses.KW_ONLY
    fill_mode: t.Literal["fit", "stretch", "zoom"] = "fit"
    on_error: EventHandler[[]] = None
    corner_radius: float | tuple[float, float, float, float] = 0
    accessibility_description: str = ""

    def __init__(
        self,
        image: ImageLike,
        *,
        fill_mode: t.Literal["fit", "stretch", "zoom"] = "fit",
        on_error: EventHandler[[]] | None = None,
        corner_radius: float | tuple[float, float, float, float] = 0,
        accessibility_description: str = "",
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_width: float = 2,
        min_height: float = 2,
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

        self.image = image
        self.fill_mode = fill_mode
        self.on_error = on_error
        self.corner_radius = corner_radius
        self.accessibility_description = accessibility_description

    def _get_image_asset(self) -> assets.Asset:
        image = self.image

        if getattr(self, "_image_for_cached_asset", None) != image:
            self._cached_image_asset = assets.Asset.from_image(image)
            self._image_for_cached_asset = image

        return self._cached_image_asset

    def _custom_serialize_(self) -> JsonDoc:
        if isinstance(self.corner_radius, (int, float)):
            corner_radius = (self.corner_radius,) * 4
        else:
            corner_radius = self.corner_radius

        return {
            "imageUrl": self._get_image_asset()._serialize(self.session),
            "reportError": self.on_error is not None,
            "corner_radius": corner_radius,
        }

    async def _on_message_(self, message: Jsonable) -> None:
        await self.call_event_handler(self.on_error)


Image._unique_id_ = "Image-builtin"
