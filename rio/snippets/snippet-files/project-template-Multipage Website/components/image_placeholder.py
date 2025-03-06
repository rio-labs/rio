from __future__ import annotations

# <additional-imports>
import rio

from .. import theme

# </additional-imports>


# <component>
class ImagePlaceholder(rio.Component):
    """
    A component that displays an image placeholder.

    The placeholder consists of a nested rectangle structure to provide styling,
    borders, and an image background.


    ## Attributes:

    `image_min_height`: The minimum height for the placeholder image.
    """

    image_min_height: float

    def build(self) -> rio.Component:
        """
        Builds the image placeholder component.

        The placeholder includes:
        - An inner rectangle containing the image with specific styling (corner
          radius and zoom fill mode).
        - An outer rectangle providing additional styling, such as a stroke and
        neutral fill.
        """
        # # Outer rectangle
        return rio.Rectangle(
            # Inner rectangle containing the image
            content=rio.Rectangle(
                content=rio.Image(
                    self.session.assets / "background_gray_2_1.svg",
                    min_height=self.image_min_height,
                    corner_radius=self.session.theme.corner_radius_medium,
                    fill_mode="zoom",
                ),
                fill=rio.Color.TRANSPARENT,
                corner_radius=self.session.theme.corner_radius_medium,
                # Add stroke to the inner rectangle
                stroke_width=0.1,
                # Semi-transparent stroke color
                stroke_color=rio.Color.from_hex("979797").replace(opacity=0.4),
                margin=1,  # Margin around the inner rectangle
            ),
            fill=self.session.theme.neutral_color,
            corner_radius=self.session.theme.corner_radius_medium,
            # Add stroke to the outer rectangle
            stroke_width=0.1,
            stroke_color=theme.NEUTRAL_COLOR_BRIGHTER,
        )


# </component>
