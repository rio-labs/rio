from __future__ import annotations

import rio

from ... import components as comps
from ... import data_models, utils

# <component>
# Select the first blog post from the list of blog posts
ACTUAL_BLOG_POST: data_models.BlogPost = utils.BLOG_POSTS[1]

# List of image URLs to be used in the page
image_url: list[str] = [
    "https://images.pexels.com/photos/5366526/pexels-photo-5366526.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    "https://images.pexels.com/photos/2724664/pexels-photo-2724664.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    "https://images.pexels.com/photos/4969837/pexels-photo-4969837.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    "https://images.pexels.com/photos/24604765/pexels-photo-24604765/free-photo-of-wanderer-steht-am-see-und-blickt-auf-das-matterhorn.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    "https://images.pexels.com/photos/2444429/pexels-photo-2444429.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
]


@rio.page(
    name="Water and Healing Power of Stones",
    url_segment="water-and-healing-power-of-stones",
)
class WaterAndHealingPowerOfStones(rio.Component):
    """
    WaterAndHealingPowerOfStones Page Component.

    Displays content about water and healing stones with a responsive layout
    that adapts between desktop and mobile views.
    """

    def build(self) -> rio.Component:
        device = self.session[data_models.PageLayout].device

        if device == "desktop":
            min_img_width = 35  # Fixed image width for desktop
            min_img_height = 20  # Fixed image height for desktop
            spacing = 2  # Spacing between images for desktop
        else:
            min_img_width = 21.2  # Fixed image width for mobile
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
                comps.BlogHeader(blog_post=ACTUAL_BLOG_POST),
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
                comps.BlogHeader(blog_post=ACTUAL_BLOG_POST),
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
