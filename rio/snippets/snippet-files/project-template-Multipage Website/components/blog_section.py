from __future__ import annotations

# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, utils

# </additional-imports>


# <component>
class BlogSection(rio.Component):
    """
    A responsive section displaying a list of blog posts.
    """

    def _desktop_build(self) -> rio.Component:
        """
        Build the layout optimized for desktop devices.

        The desktop layout includes:
        - A major blog post displayed prominently.
        - Minor blog posts organized into three columns.
        - Proper spacing and alignment for desktop readability.
        """
        # Space between elements
        spacing = 4

        # Initialize three columns to distribute blog posts evenly
        column_1 = rio.Column(spacing=spacing)
        column_2 = rio.Column(spacing=spacing)
        column_3 = rio.Column(spacing=spacing)

        # Get all posts except the first one
        minor_posts = list(utils.BLOG_POSTS_BY_URL.values())[1:]
        total_posts = len(minor_posts)

        # Basic distribution (minimum posts per column)
        base_per_column = total_posts // 3

        # Calculate remaining posts to distribute
        remaining = total_posts % 3

        # Calculate actual posts per column
        col1_posts = base_per_column + (1 if remaining > 0 else 0)
        col2_posts = base_per_column + (1 if remaining > 1 else 0)

        # Distribute posts using calculated positions
        for post in minor_posts[:col1_posts]:
            column_1.add(comps.BlogMinor(post, spacing=spacing))

        for post in minor_posts[col1_posts : col1_posts + col2_posts]:
            column_2.add(comps.BlogMinor(post, spacing=spacing))

        for post in minor_posts[col1_posts + col2_posts :]:
            column_3.add(comps.BlogMinor(post, spacing=spacing))

        # Add spacers to columns to ensure equal positioning if needed
        column_1.add(rio.Spacer())
        column_2.add(rio.Spacer())
        column_3.add(rio.Spacer())

        # Combine the columns into a single row
        content = rio.Row(
            column_1,
            column_2,
            column_3,
            spacing=spacing,
        )

        # Return the full blog section with the major post and the content row
        return rio.Column(
            comps.BlogMajor(
                # The major blog post (post 0)
                list(utils.BLOG_POSTS_BY_URL.values())[0],
                margin_y=2,  # Vertical margin around the major post
            ),
            # Add the minor blog posts
            content,
            spacing=spacing,  # Space between the major post and the content row
        )

    def _mobile_build(self) -> rio.Component:
        """
        Builds the column layout optimized for mobile devices.

        The mobile layout includes:
        - All blog posts displayed in a single column.
        """
        # Reduced spacing for mobile devices
        content = rio.Column(spacing=1)

        # Add all blog posts as minor posts to the content column
        for post in utils.BLOG_POSTS_BY_URL.values():
            content.add(
                comps.BlogMinor(
                    post,
                ),
            )
        return content

    def build(self) -> rio.Component:
        """
        Build and return the page layout based on the user's device type.

        Determines whether the user is on a desktop or mobile device and builds
        the corresponding layout.
        """
        device = self.session[data_models.PageLayout].device

        if device == "desktop":
            # Build and return the desktop-optimized layout
            return self._desktop_build()

        else:
            # Build and return the mobile-optimized layout
            return self._mobile_build()


# </component>
