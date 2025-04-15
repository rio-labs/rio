from __future__ import annotations

# <additional-imports>
import rio

from ... import components as comps
from ... import data_models, theme

# </additional-imports>

# <component>
# After creating our blog page that returns a `rio.PageView` and its
# corresponding sub-page directory, we can now set up a blog section to display
# the blog posts. Since `blog_page.py` has the `url_segment` "blog", we can
# designate the blog home page as the parent of the blog posts by setting its
# `url_segment` to an empty string. This makes the blog home page the parent
# page of all blog posts. Therefore, the url of the blog home page will be
# "website.com/blog". The blog posts will have urls like
# "website.com/blog/post1".


@rio.page(
    name="blog",
    url_segment="",
)
class BlogPage(rio.Component):
    """
    The blog home page.

    This page serves as the main hub for all blog posts. It displays an
    introductory section and a list of blog posts. As the parent page, it
    organizes and manages the URLs for individual blog entries.
    """

    def _desktop_build(self) -> rio.Component:
        """
        Build the layout optimized for desktop devices.
        """
        return rio.Column(
            rio.Text(
                "Blog",
                style=theme.BOLD_BIGGER_SECTION_TITLE_DESKTOP,
            ),
            rio.Text(
                "Welcome to our blog. Here you can find all the latest news and updates.",
                style=theme.DARK_TEXT_BIGGER,
            ),
            rio.Separator(
                color=self.session.theme.neutral_color,
                margin_top=3,
            ),
            comps.BlogSection(),
            spacing=1,  # Space between components for desktop view
            align_x=0.5,  # Center horizontally
            align_y=0,  # Align to the top vertically
            min_width=80,  # Fixed width to ensure proper layout on larger screens
        )

    def _mobile_build(self) -> rio.Component:
        """
        Build the layout optimized for mobile devices.
        """
        return rio.Column(
            rio.Text(
                "Blog",
                overflow="wrap",
                style=theme.BOLD_BIGGER_SECTION_TITLE_MOBILE,
            ),
            rio.Text(
                "Welcome to our blog. Here you can find all the latest news and updates.",
                overflow="wrap",
                style=theme.DARK_TEXT_BIGGER,
            ),
            rio.Separator(
                color=theme.SEPARATOR_COLOR,
                margin_top=3,
            ),
            # Add the BlogSection component to display the blog posts
            comps.BlogSection(),
            align_y=0,  # Align to the top vertically
            spacing=1,  # Space between components for mobile view
            margin_x=1,  # Horizontal margin for mobile screens
        )

    def build(self) -> rio.Component:
        """
        Construct and return the page layout based on the user's device type.

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
