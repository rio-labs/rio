import rio


# <component>
class ColoredRectangle(rio.Component):
    """
    A component that displays a rectangle with a specific color based on its content.

    The color of the rectangle is determined by the `content` value. If the content
    is "Unsubscribed", "Subscribed", or "Bounced", a predefined color is used. Otherwise,
    a custom color must be provided via the `color` attribute.


    ## Attributes:

    `content`: The content displayed in the rectangle, which determines its
    color.

    `color`: A custom color for the rectangle, required if the content
    does not match predefined values.
    """

    content: int | str
    color: rio.Color | None = None

    def build(self) -> rio.Component:
        # Determine the color based on the content
        if self.content == "Unsubscribed":
            color = rio.Color.from_hex("#FF6B6B")

        elif self.content == "Subscribed":
            color = rio.Color.from_hex("#4CAF50")

        elif self.content == "Bounced":
            color = rio.Color.from_hex("#FFA500")

        # If the content does not match predefined values, use the custom color
        else:
            assert self.color is not None
            color = self.color

        return rio.Rectangle(
            content=rio.Text(
                str(self.content),
                fill=color,
                font_size=0.7,
                margin=0.2,
                margin_x=0.5,
            ),
            fill=color.replace(opacity=0.2),
            stroke_color=color,
            stroke_width=0.1,
            corner_radius=self.session.theme.corner_radius_small,
            align_x=0,
            align_y=0.5,
        )


# </component>
