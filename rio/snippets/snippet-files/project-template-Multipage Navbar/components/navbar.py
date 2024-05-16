# <additional-imports>

import rio

# </additional-imports>

# <component>
class NavBar(rio.Component):
    """
    A navbar with a fixed position and responsive width.
    """
    def build(self) -> rio.Component:
        return rio.Overlay(
            rio.Row(
                rio.Spacer(),
                rio.Card(
                    rio.Row(
                        rio.Button(
                            rio.Link(
                                "Home",
                                ('/'),
                            )
                        ),
                        rio.Spacer(),
                        rio.Button(
                            rio.Link(
                                "About",
                                ('/about-page'),
                            )
                        ),
                        margin=1,
                    ),
                    color=rio.Color.from_hex("333333ff"),
                ),
                rio.Spacer(),
                proportions=(0.5, 9, 0.5),
                align_y=0.05,
                margin=1
            )
        )
# </component>
