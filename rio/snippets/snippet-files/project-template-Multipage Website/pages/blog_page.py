from __future__ import annotations

# <additional-imports>
import rio

# </additional-imports>


# <component>
@rio.page(
    name="Blog",
    url_segment="blog",
)
class BlogPage(rio.Component):
    """
    This page will be used as the root component for blog pages. This means,
    that it will always be visible, regardless of which sub page is currently
    active.

    Similar to the root component the blog page contains a `rio.PageView`. Page
    views don't have any appearance on their own, but they are used to display
    the content of the currently active page.
    """

    def build(self) -> rio.Component:
        return rio.PageView()


# </component>
