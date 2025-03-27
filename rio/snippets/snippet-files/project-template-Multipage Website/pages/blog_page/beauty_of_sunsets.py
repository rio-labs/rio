from __future__ import annotations

# <additional-imports>
import rio

from ... import components as comps
from ... import data_models, utils

# </additional-imports>

# <component>
# List of image URLs to be used in the page
image_url: list[str] = [
    "https://images.pexels.com/photos/248159/pexels-photo-248159.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    "https://images.pexels.com/photos/206359/pexels-photo-206359.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
]


@rio.page(
    name="Beauty of Sunsets",
    url_segment="beauty-of-sunsets",
)
class BeautyOfSunsets(rio.Component):
    """
    Displays sample content with a responsive layout that adapts between desktop
    and mobile views.
    """

    def build(self) -> rio.Component:
        # Retrieve the device type from the session data
        device = self.session[data_models.PageLayout].device

        # get the URL name of the active page
        url_name = self.session.active_page_url.name
        # Get single blog post by URL key
        blog_post = utils.BLOG_POSTS_BY_URL["/" + url_name]

        if device == "desktop":
            min_img_width = 35  # Fixed image width for desktop
            min_img_height = 20  # Fixed image height for desktop
            spacing = 2  # Spacing between images for desktop
        else:
            margin_x = 1
            # Calculate the minimum image width for mobile based on the window
            # width and margin
            min_img_width = self.session.window_width - margin_x * 2
            min_img_height = 13  # Fixed image height for mobile
            spacing = 0.5  # Spacing between images for mobile

        # Create the markdown content
        markdown_content = rio.Markdown(
            """
# Lorem ipsum dolor sit amet, consetetur sadipscing elitr

Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie
consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan
et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis
dolore te feugait nulla facilisi. Lorem ipsum dolor sit amet, consectetuer
adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna
aliquam erat volutpat.

Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit
lobortis nisl ut aliquip ex ea commodo consequat. Duis autem vel eum iriure
dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore
eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui
blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla
facilisi.
            """
        )

        # Create the image content
        image_content = rio.Image(
            rio.URL(image_url[0]),
            fill_mode="zoom",
            corner_radius=self.session.theme.corner_radius_medium,
            min_width=min_img_width,
            min_height=min_img_height,
        )

        markdown_content2 = rio.Markdown(
            """
# Lorem ipsum dolor sit amet, consetetur sadipscing elitr

Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie
consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan
et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis
dolore te feugait nulla facilisi. Lorem ipsum dolor sit amet, consectetuer
adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna
aliquam erat volutpat.

Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit
lobortis nisl ut aliquip ex ea commodo consequat. Duis autem vel eum iriure
dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore
eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui
blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla
facilisi.
            """
        )

        # Create the second image content
        image_content2 = rio.Image(
            rio.URL(image_url[1]),
            fill_mode="zoom",
            corner_radius=self.session.theme.corner_radius_medium,
            min_width=min_img_width,
            min_height=min_img_height,
        )

        # Create the main content based on device type
        if device == "desktop":
            content = rio.Column(
                comps.BlogHeader(blog_post=blog_post),
                rio.Row(
                    markdown_content,
                    image_content,
                    spacing=spacing,
                ),
                rio.Row(
                    image_content2,
                    markdown_content2,
                    spacing=spacing,
                ),
                spacing=4,  # Increased spacing between rows for better readability
            )
        else:
            content = rio.Column(
                comps.BlogHeader(blog_post=blog_post),
                markdown_content,
                image_content,
                markdown_content2,  # Fixed: Using markdown_content2 instead of duplicate
                image_content2,  # Fixed: Using image_content2 instead of duplicate
                spacing=spacing,
            )

        # Return the appropriate container based on device type
        if device == "desktop":
            return rio.Container(
                content=content,
                align_x=0.5,  # Center the container horizontally
                min_width=80,  # Fixed width for desktop layout
            )
        else:
            return rio.Container(
                content=content,
                margin_x=1,  # Horizontal margin for mobile layout
            )


# </component>
