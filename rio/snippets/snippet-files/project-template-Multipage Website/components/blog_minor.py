from __future__ import annotations

# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, theme

# </additional-imports>


# <component>
class BlogMinor(rio.Component):
    """
    A component to display a single blog post in a smaller format.


    ## Attributes:

    `blog_post`: Represents the blog post data including title, description,
    image, and other metadata.

    `spacing`: The spacing between blog posts, used to calculate image width for
    desktop layout.
    """

    blog_post: data_models.BlogPost
    spacing: float = 4

    def build(self) -> rio.Component:
        """
        Builds the BlogMinor component.

        The layout adjusts based on the device type:
        - Desktop: Larger images and font sizes, calculated dynamically based on spacing.
        - Mobile: Smaller, static image widths and font sizes.
        """
        # Get the user's device type
        device = self.session[data_models.PageLayout].device
        # Determine device type and adjust sizes accordingly
        if device == "desktop":
            # Dynamically calculate image width for desktop layout
            min_img_width = (80 - 2 * self.spacing) / 3
            blog_post_title_font_size = 1.4
            blog_post_description_text_style = theme.DARK_TEXT_BIGGER

        else:
            min_img_width = (
                self.session.window_width - 2
            )  # substraction of margin_x
            blog_post_title_font_size = 1.2
            blog_post_description_text_style = theme.DARKER_TEXT

        # Content container for the blog post
        content = rio.Column(spacing=2)

        # Add the image
        content.add(
            rio.Rectangle(
                fill=rio.ImageFill(
                    rio.URL(self.blog_post.image),
                    fill_mode="zoom",
                ),
                # Add a fine border around the image
                stroke_width=0.1,
                stroke_color=self.session.theme.neutral_color,
                corner_radius=self.session.theme.corner_radius_medium,
                # Set the cursor to a pointer on hover
                cursor="pointer",
                # Set alignment and size of rectangle
                align_x=0,  # Left align
                align_y=0,  # Top align
                min_height=15,  # Fixed height
                min_width=min_img_width,  # Fixed width
            ),
        )

        # Add the content Column, containing the category, title, description,
        # author image and date
        content.add(
            rio.Column(
                # Category button, does not redirect to a page
                comps.OutlinedColoredButton(
                    text=self.blog_post.category,
                    corner_radius=self.session.theme.corner_radius_small,
                    font_size=0.8,
                    font_weight="normal",
                    margin_x_row=0.5,
                    margin_y_row=0.3,
                    align_x=0,
                ),
                # Add the title
                rio.Text(
                    self.blog_post.title,
                    font_size=blog_post_title_font_size,
                    font_weight="bold",
                ),
                # Add the description
                rio.Text(
                    self.blog_post.description,
                    overflow="wrap",
                    style=blog_post_description_text_style,
                ),
                rio.Row(
                    # Display the author image as a circle
                    rio.Rectangle(
                        # author image
                        fill=rio.ImageFill(
                            self.session.assets / self.blog_post.author_image
                        ),
                        corner_radius=99999,  # Fully rounded for circular appearance
                        cursor="pointer",  # Pointer cursor for interactivity
                        stroke_width=0.1,  # Thin border around the circle
                        stroke_color=theme.NEUTRAL_COLOR_BRIGHTER,  # Light border color
                        hover_stroke_color=self.session.theme.primary_color,
                        min_height=2,
                        min_width=2,
                        align_x=0,
                        align_y=0.5,
                    ),
                    # Display the date of the blog post
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
                min_width=20,  # Minimum width for the column
                spacing=1,  # Space between elements
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
            # + "/adventure-in-the-swiss-alps",
            + self.blog_post.url_segment,
            # TODO: change fixed string to + self.blog_post.url_segment if all
            # blog posts have a page
        )


# </component>
