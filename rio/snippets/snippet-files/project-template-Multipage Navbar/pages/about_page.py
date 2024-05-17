from typing import *  # type:ignore

import rio

# <additional-imports>
from .. import components as comps

# </additional-imports>


# <component>
class AboutPage(rio.Component):
    """
    This is an example Page for the about page. 
    Pages are identical to other Components and only differ in how they're used.
    """

    def build(self) -> rio.Component:
        return rio.Column(
            comps.Navbar(),
            rio.Text("My App - About page", style="heading2"),
            rio.Text(
                "This is a sample page. Replace it with your own content."
            ),
            spacing=2,
            margin=2,
            align_y=0.5,
        )



# </component>
