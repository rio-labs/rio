from __future__ import annotations

# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, theme

# </additional-imports>


# <component>
class BlogMajor(rio.Component):
    """
    A component to display a major blog post with prominent styling and layout.


    ## Attributes:

    `blog_post`: Represents the blog post data, including title, description,
    image, and metadata.
    """

    blog_post: data_models.BlogPost

    def build(self) -> rio.Component:
        """
        Constructs the BlogMajor component.

        The layout includes:
        - A large featured image for the blog post.
        - Category, title, description, and metadata styled prominently.
        - Responsive alignment and spacing to highlight the blog post.
        """
        # Row container for the major blog post
        content = rio.Row(spacing=2)

        # Add the featured image
        content.add(
            rio.Column(
                rio.Rectangle(
                    fill=rio.ImageFill(
                        rio.URL(self.blog_post.image),
                        fill_mode="zoom",
                    ),
                    # Add a thin border around the image
                    stroke_width=0.1,
                    stroke_color=self.session.theme.neutral_color,
                    corner_radius=self.session.theme.corner_radius_medium,
                    cursor="pointer",
                    align_x=0,  # Align image to the left
                    align_y=0,  # Align image to the top
                    min_height=25,  # Fixed height for the image
                    min_width=40,  # Fixed width for the image
                ),
            )
        )

        # Add the content section with category, title, description, and metadata
        content.add(
            rio.Column(
                # Category button
                comps.OutlinedColoredButton(
                    text=self.blog_post.category,
                    corner_radius=self.session.theme.corner_radius_small,
                    font_size=0.8,  # Smaller font size for category
                    font_weight="normal",  # Normal font weight
                    margin_x_row=0.5,  # Horizontal margin within the button
                    margin_y_row=0.3,  # Vertical margin within the button
                    align_x=0,  # Align button to the left
                ),
                # Blog post title
                rio.Text(
                    self.blog_post.title,
                    font_size=1.4,
                    font_weight="bold",
                ),
                # Blog post description
                rio.Text(
                    self.blog_post.description,
                    overflow="wrap",  # Allow text wrapping if needed
                    style=theme.DARK_TEXT_BIGGER,
                ),
                # Row for author image and metadata
                rio.Row(
                    rio.Rectangle(
                        # fill=self.session.theme.primary_color,
                        fill=rio.ImageFill(
                            self.session.assets / self.blog_post.author_image
                        ),
                        corner_radius=99999,
                        cursor="pointer",
                        stroke_width=0.1,
                        stroke_color=theme.NEUTRAL_COLOR_BRIGHTER,
                        hover_stroke_color=self.session.theme.primary_color,
                        min_height=2,
                        min_width=2,
                        align_x=0,
                        align_y=0.5,
                    ),
                    rio.Text(
                        self.blog_post.date,
                        style=theme.DARKER_TEXT,
                        align_y=0.5,  # Vertically center-align the text
                    ),
                    spacing=1,  # Space between image and text
                    align_x=0,  # Align row to the left
                ),
                align_x=0,  # Align column content to the left
                align_y=0.5,  # Vertically center-align the column
                min_width=35,  # Fixed width for the column
                spacing=1,  # Space between elements in the column
            )
        )

        # Return the clickable blog post as a link
        return rio.Link(
            content=rio.Rectangle(
                content=content,
                fill=rio.Color.TRANSPARENT,
                cursor="pointer",
            ),
            # Navigate to the blog post's URL when clicked
            target_url=str(self.session.active_page_url)
            + self.blog_post.url_segment,
        )


# </component>
