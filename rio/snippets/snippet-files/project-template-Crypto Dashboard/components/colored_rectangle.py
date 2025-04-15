import rio


# <component>
class ColoredRectangle(rio.Component):
    """
     A component that represents a rectangle with a color and text indicating a
     percentage difference.


    ## Attributes:

    `percentage_difference`: The percentage difference to display in the
        rectangle. Positive values are displayed in green, while negative values
        are displayed in red.
    """

    percentage_difference: float

    def build(self) -> rio.Component:
        # Determine the color according of the percentage difference.
        if self.percentage_difference > 0:
            color = rio.Color.GREEN
        else:
            color = rio.Color.RED

        # Return a rectangle component with the appropriate styling and content
        return rio.Rectangle(
            content=rio.Text(
                text=f"{self.percentage_difference:,.2f} %",
                fill=color,
                font_size=self.session.theme.text_style.font_size * 0.9,
                margin=0.2,
            ),
            # Set a semi-transparent fill color for the rectangle
            fill=color.replace(opacity=0.1),
            stroke_color=color,
            stroke_width=0.1,
            align_y=0.5,
            corner_radius=self.session.theme.corner_radius_small,
        )


# </component>
