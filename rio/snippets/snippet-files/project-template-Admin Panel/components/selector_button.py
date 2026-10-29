import rio

# <additional-imports>
from .. import components as comps
from .. import theme

# </additional-imports>


# <component>
class SelectorButton(rio.Component):
    """
    A button that is used to change the page.


    ## Attributes:

    `section`: The name of the section that the button will navigate to.

    `section_icon`: The icon that will be displayed next to the section name.

    `section_url_fragment`: The URL fragment that the button will navigate to.

    `is_active`: A boolean that determines if the button is active or not.
    """

    section: str
    section_icon: str
    section_url_fragment: str

    is_active: bool = False

    def build(self) -> rio.Component:
        # Change the style of the button based on whether it is active or not
        if self.is_active:
            style = rio.TextStyle(
                fill=theme.TEXT_FILL_BRIGHTER,
                font_weight="bold",
                font_size=0.9,
            )
            icon_fill = theme.TEXT_FILL_BRIGHTER
            rectangle_fill = self.session.theme.primary_color

        else:
            style = rio.TextStyle(
                fill=theme.TEXT_FILL_DARKER,
                font_size=0.9,
            )
            icon_fill = theme.TEXT_FILL_DARKER
            rectangle_fill = rio.Color.TRANSPARENT

        return rio.Link(
            rio.Rectangle(
                content=rio.Column(
                    comps.HoverCard(
                        section=self.section,
                        icon=self.section_icon,
                        text_style=style,
                        icon_fill=icon_fill,
                        grow_y=True,
                    ),
                    # Add a rectangle to the bottom of the button to indicate
                    # that it is active or not
                    rio.Rectangle(
                        fill=rectangle_fill,
                        align_y=1,
                        min_height=0.2,
                        transition_time=0,
                    ),
                    align_y=0,
                    min_height=3.5,
                ),
                fill=rio.Color.TRANSPARENT,
                cursor="pointer",
            ),
            target_url=self.section_url_fragment,
        )


# </component>
