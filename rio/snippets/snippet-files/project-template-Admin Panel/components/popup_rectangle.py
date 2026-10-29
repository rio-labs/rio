import rio


# <component>
class PopupRectangle(rio.Component):
    """
    A component that represents a popup rectangle with customizable content.

    This component displays a rectangle with a specified content component
    inside it. The rectangle is styled using the application's theme, including
    its fill color, stroke color, and corner radius.


    ## Attributes:

    `content`: The content to be displayed inside the rectangle.
    """

    content: rio.Component

    def build(self) -> rio.Component:
        return rio.Rectangle(
            content=self.content,
            fill=self.session.theme.neutral_color,
            stroke_width=0.1,
            stroke_color=self.session.theme.neutral_color.brighter(0.2),
            corner_radius=self.session.theme.corner_radius_small,
        )


# </component>
