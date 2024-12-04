from __future__ import annotations

# <additional-imports>
import rio

from .. import theme

# </additional-imports>


# <component>
class Testimonial(rio.Component):
    """
    Testimonial Component.

    This component displays 100% legitimate testimonials from real, totally not
    made-up people, including their quote, name, and company. It is styled
    within a `rio.Rectangle` to stand out from the background, providing a
    visually appealing and organized presentation of customer feedback.

    ## Attributes:

    `img`: The image of the person who said the quote.

    `quote`: The quote somebody has definitely said about this company.

    `name`: Who said the quote, probably Mark Twain.

    `company`: The company the person is from.
    """

    img: str
    quote: str
    name: str
    company: str

    def build(self) -> rio.Component:
        # Wrap the testimonial content in a styled rectangle to make it stand
        # out
        return rio.Rectangle(
            # Content of the rectangle arranged in a vertical column
            content=rio.Column(
                # Display the testimonial quote using Markdown for rich text
                # formatting
                rio.Markdown(self.quote),
                # Row containing a image of the customer and customer
                # information
                rio.Row(
                    rio.Rectangle(
                        align_x=0.5,  # Center the circle horizontally within the row
                        align_y=0.5,  # Center the circle vertically within the row
                        min_width=3,  # Fixed width of the circle
                        min_height=3,  # Fixed height of the circle
                        corner_radius=99999,  # Fully rounded corners to create a perfect circle
                        fill=rio.ImageFill(self.session.assets / self.img),
                        # Add a border around the circle
                        stroke_width=0.1,
                        stroke_color=theme.NEUTRAL_COLOR_BRIGHTER,
                    ),
                    # Column containing the customer's name and company
                    rio.Column(
                        rio.Text(
                            self.name,
                        ),
                        rio.Text(
                            self.company,
                            # Dimmed text for less prominent information
                            style="dim",
                        ),
                    ),
                    align_x=0,  # Align the row contents to the start horizontally
                    spacing=1,  # Space between the decorative circle and customer info
                ),
                spacing=1,  # Space between the quote and the customer info row
                margin=2,  # Margin around the content within the column
                align_y=0.5,  # Vertically center the column within the card
            ),
            fill=self.session.theme.neutral_color,
            # Add a corner radius to the rectangle to create medium rounded
            # corners
            corner_radius=self.session.theme.corner_radius_medium,
            # Add a border around the rectangle to separate it from the
            # background
            stroke_width=0.1,
            # Border color slightly brighter than background.
            stroke_color=theme.NEUTRAL_COLOR_BRIGHTER,
        )


# </component>
