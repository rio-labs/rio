from __future__ import annotations

# <additional-imports>
import rio

from .. import data_models, theme

# </additional-imports>


# <component>
class AuthorCard(rio.Component):
    """
    A component to display an author's details in a visually appealing card format.


    ## Attributes:

    `blog_post`: The blog post data, including the author's name.
    """

    blog_post: data_models.BlogPost

    def build(self) -> rio.Component:
        """
        Build the AuthorCard component.

        The layout includes:
        - A circular avatar placeholder.
        - The author's name displayed next to the avatar.
        - Proper alignment, spacing, and styling for consistency.
        """
        # Row container for the author's avatar and name
        content = rio.Row(
            rio.Rectangle(
                fill=rio.ImageFill(
                    self.session.assets / self.blog_post.author_image
                ),
                corner_radius=9999,  # Fully rounded corners for a circular appearance
                # Add stroke
                stroke_width=0.1,
                stroke_color=theme.NEUTRAL_COLOR_BRIGHTER,
                align_x=0.5,
                align_y=0.5,
                min_width=1.4,
                min_height=1.4,
            ),
            # Text displaying the author's name
            rio.Text(
                self.blog_post.author,
                font_size=self.session.theme.text_style.font_size * 0.9,
                font_weight="bold",
                align_y=0.5,  # Vertically center-align the text
            ),
            spacing=0.5,  # Space between the avatar and the name
            margin=0.4,  # Margin around the row content
        )

        # Return the AuthorCard wrapped in a rectangle for styling
        return rio.Rectangle(
            content=content,
            fill=rio.Color.TRANSPARENT,
            # Add border styling
            stroke_width=0.1,
            stroke_color=theme.NEUTRAL_COLOR_BRIGHTER,
            corner_radius=9999,  # Rounded corners for the card
            align_x=0,  # Align the card to the left
            align_y=0,  # Align the card vertically to the top
        )


# </component>
