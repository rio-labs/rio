from __future__ import annotations

# <additional-imports>
import rio

from ... import components as comps
from ... import data_models, utils

# </additional-imports>


# <component>
# List of image URLs to be used in the AdventureInAlps page
image_url: list[str] = [
    "https://images.pexels.com/photos/5366526/pexels-photo-5366526.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    "https://images.pexels.com/photos/2724664/pexels-photo-2724664.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    "https://images.pexels.com/photos/4969837/pexels-photo-4969837.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    "https://images.pexels.com/photos/24604765/pexels-photo-24604765/free-photo-of-wanderer-steht-am-see-und-blickt-auf-das-matterhorn.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    "https://images.pexels.com/photos/2444429/pexels-photo-2444429.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
]


@rio.page(
    name="adventure",
    url_segment="adventure-in-the-swiss-alps",
)
class AdventureInAlps(rio.Component):
    """
    AdventureInAlps Page Component.

    This page showcases an adventure in the Swiss Alps, including a "detailed
    descriptions" and images to engage users.
    """

    def build(self) -> rio.Component:
        # Retrieve the device type from the session data
        device = self.session[data_models.PageLayout].device

        # get the URL name of the active page
        url_name = self.session.active_page_url.name
        # Get single blog post by URL key
        blog_post = utils.BLOG_POSTS_BY_URL["/" + url_name]

        # Define layout parameters based on device type
        if device == "desktop":
            min_img_width = 80  # Fixed image width for desktop
            min_img_height = 40  # Fixed image height for desktop
            min_img_height_row = (
                20  # Fixed image height within a row for desktop
            )
            spacing = 2  # Spacing between images for desktop

        else:
            margin_x = 1
            # Calculate the minimum image width for mobile based on the window
            # width and margin
            min_img_width = self.session.window_width - margin_x * 2
            min_img_height = 13  # Fixed image height for mobile
            min_img_height_row = 7  # Fixed image height within a row for mobile
            spacing = 0.5  # Spacing between images for mobile

        # Calculate image width within a row based on spacing and number of
        # images
        min_img_width_row = (min_img_width - 3 * spacing) / 4

        # Create a row to hold multiple images
        image_content = rio.Row(spacing=spacing)
        # Ignore the first image in the list as it is displayed separately
        for i in range(1, len(image_url)):
            image_content.add(
                rio.Image(
                    rio.URL(image_url[i]),
                    fill_mode="stretch",
                    corner_radius=self.session.theme.corner_radius_medium,
                    min_width=min_img_width_row,
                    min_height=min_img_height_row,
                )
            )

        # Construct the main content column
        content = rio.Column(
            comps.BlogHeader(blog_post),
            rio.Markdown(
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
            ),
            # Add the first image separately with a larger size
            rio.Image(
                rio.URL(image_url[0]),
                fill_mode="stretch",
                corner_radius=self.session.theme.corner_radius_medium,
                min_width=min_img_width,
                min_height=min_img_height,
            ),
            rio.Markdown(
                """
## Lorem ipsum dolor sit amet, consetetur sadipscing elitr

Nam liber tempor cum soluta nobis eleifend option congue nihil imperdiet doming
id quod mazim placerat facer possim assum. Lorem ipsum dolor sit amet,
consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet
dolore magna aliquam erat volutpat. Ut wisi enim ad minim veniam, quis nostrud
exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo
consequat. 

At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd
gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum
dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor
invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos
et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea
takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet,
consetetur sadipscing elitr, At accusam aliquyam diam diam dolore dolores duo
eirmod eos erat, et nonumy sed tempor et et invidunt justo labore Stet clita ea
et gubergren, kasd magna no rebum. sanctus sea sed takimata ut vero voluptua.
est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur
sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore
magna aliquyam erat. 
"""
            ),
            # Add the image row content
            image_content,
            rio.Markdown(
                """
## Lorem ipsum dolor sit amet, consetetur sadipscing elitr

Consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et
dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo
duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est
Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing
elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam
erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea
rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor
sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita
kasd gubergren, no sea takimata sanctus. 

Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie
consequat, vel illum dolore eu feugiat nulla facilisis. 
"""
            ),
            spacing=2,
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
