from __future__ import annotations

from dataclasses import KW_ONLY
from typing import Literal, final

from uniserde import Jsonable, JsonDoc

from .. import assets
from ..utils import EventHandler, ImageLike
from .fundamental_component import FundamentalComponent

__all__ = ["Image"]


@final
class Image(FundamentalComponent):
    """
    Displays a raster image or SVG.

    `Image` does just what you'd expect: it displays a single image. The image
    can be loaded from a URL or a local file.

    Note that the resolution of the image does not affect the size at which it
    is displayed. The `Image` component is flexible with its space requirements,
    it adapts to the space allocated by its parent component.

    The image can be scaled to fit the shape in one of three ways:

    - `fit`: The image is scaled to fit entirely inside the shape, while
      maintaining its aspect ratio. This is the default.
    - `stretch`: The image is stretched to fill the shape, distorting it if
      necessary.
    - `zoom`: The image is scaled to fill the shape entirely, while maintaining
      its aspect ratio. This may cause the image to overflow the shape.


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


    ## Examples

    This minimal example will simply display an image with the URL
    "https://example.com/image.png":

    ```python
    rio.Image(rio.URL("https://example.com/image.png"))
    ```

    This example demonstrates how to display an `Image` using a Path object.
    The image will be scaled to fit the shape, and the corners will be rounded
    with a radius of 2:

    ```python
    from pathlib import Path

    rio.Image(
        Path("example_image.png"),
        fill_mode="fit",
        width=20,
        height=20,
        corner_radius=2,
    )
    ```
    """

    image: ImageLike
    _: KW_ONLY
    fill_mode: Literal["fit", "stretch", "zoom"] = "fit"
    on_error: EventHandler[[]] = None
    corner_radius: float | tuple[float, float, float, float] = 0

    def _get_image_asset(self) -> assets.Asset:
        image = self.image

        if getattr(self, "_image_for_cached_asset", None) != image:
            self._cached_image_asset = assets.Asset.from_image(image)
            self._image_for_cached_asset = image

        return self._cached_image_asset

    def _custom_serialize(self) -> JsonDoc:
        if isinstance(self.corner_radius, (int, float)):
            corner_radius = (self.corner_radius,) * 4
        else:
            corner_radius = self.corner_radius

        return {
            "imageUrl": self._get_image_asset()._serialize(self.session),
            "reportError": self.on_error is not None,
            "corner_radius": corner_radius,
        }

    async def _on_message(self, message: Jsonable) -> None:
        await self.call_event_handler(self.on_error)


Image._unique_id = "Image-builtin"
