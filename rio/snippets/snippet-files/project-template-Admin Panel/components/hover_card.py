import rio

# <additional-imports>
from .. import theme

# </additional-imports>


# <component>
class HoverCard(rio.Component):
    """
    A hoverable card component that displays an icon and text.

    This component creates a rectangular card with an icon and text that changes
    appearance on hover. It supports customizable text styles and icon colors.


    ## Attributes:

    `section`: The text to display in the card

    `icon`: The name/path of the icon to display

    `text_style`: Custom text styling. If None, uses default style

    `icon_fill`: Custom icon color. If None, uses default color

    """

    section: str
    icon: str

    text_style: rio.TextStyle | None = None
    icon_fill: rio.Color | None = None

    def build(self) -> rio.Component:
        # Define the style of the text and icon
        style = self.text_style or theme.TEXT_STYLE_DARKER_SMALL

        icon_fill = self.icon_fill or theme.TEXT_FILL_DARKER

        return rio.Rectangle(
            content=rio.Row(
                rio.Icon(self.icon, fill=icon_fill),
                rio.Text(self.section, style=style),
                spacing=0.5,
                margin=0.4,
            ),
            fill=rio.Color.TRANSPARENT,
            hover_fill=self.session.theme.neutral_color,
            corner_radius=self.session.theme.corner_radius_small,
            transition_time=0.1,
            cursor="pointer",
            align_y=0.5,
        )


# </component>
