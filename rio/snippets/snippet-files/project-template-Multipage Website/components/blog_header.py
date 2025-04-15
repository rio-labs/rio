from __future__ import annotations

# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, theme

# </additional-imports>


# <component>
class BlogHeader(rio.Component):
    """
    A component to display the header of a blog post.


    ## Attributes:

    `blog_post`: The data for the blog post, including category, title,
    description, date, and author details.
    """

    blog_post: data_models.BlogPost

    def build(self) -> rio.Component:
        """
        Build the BlogHeader component.

        The layout includes:
        - A row with the category button, separator, and publication date.
        - A prominently styled title.
        - A description text.
        - An author card with metadata.
        - A separator line for distinction.
        """
        return rio.Column(
            # Row with category button, separator, and publication date
            rio.Row(
                comps.OutlinedColoredButton(
                    text=self.blog_post.category,
                    corner_radius=self.session.theme.corner_radius_small,
                    font_size=0.8,
                    font_weight="normal",
                    margin_x_row=0.5,
                    margin_y_row=0.3,
                    align_x=0,
                ),
                rio.Text(
                    "·",
                    style=theme.DARKER_TEXT,
                ),
                rio.Text(
                    self.blog_post.date,
                    style=theme.DARK_TEXT_SMALLER,
                ),
                spacing=0.5,  # Space between elements in the row
                align_x=0,  # Align row content to the left
                align_y=0,  # Align row vertically to the top
            ),
            # Blog post title
            rio.Text(
                self.blog_post.title,
                overflow="wrap",
                fill=theme.TEXT_FILL_SLIGHTLY_BRIGHTER,
                font_weight="bold",
                font_size=2,
            ),
            # Blog post description
            rio.Text(
                self.blog_post.description,
                overflow="wrap",
                fill=theme.TEXT_FILL_DARKER,
                font_size=1.2,
            ),
            # Author card with details
            comps.AuthorCard(blog_post=self.blog_post),
            # Separator line for distinction
            rio.Separator(color=self.session.theme.neutral_color),
            spacing=1,  # Space between elements in the column
        )


# </component>
