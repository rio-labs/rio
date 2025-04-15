import typing as t

# <additional-imports>
import rio

# </additional-imports>


# <component>
class OutlinedColoredButton(rio.Component):
    """
    A customizable outlined button with an optional icon and link functionality.


    ## Attributes:

    `text`: The label to display on the button.

    `target_url`: The URL to navigate to when the button is clicked. If None,
    the button acts as a static component.

    `icon`: Optional icon to display alongside the button text.

    `corner_radius`: Radius of the button's corners for rounding.

    `font_size`: Font size for the button text.

    `font_weight`: Weight of the button text font.

    `margin_x_row`: Horizontal padding for the button's content.

    `margin_y_row`: Vertical padding for the button's content.
    """

    text: str

    target_url: str | None = None
    icon: str | None = None
    corner_radius: float = 9999
    font_size: float = 1
    font_weight: t.Literal["normal", "bold"] = "bold"
    margin_x_row: float = 1
    margin_y_row: float = 0.5

    def build(self) -> rio.Component:
        """
        Builds the outlined colored button component.

        The button includes:
        - A row containing text (and optionally an icon) with customizable styling.
        - A rectangle with an outlined style, hover effects, and rounded corners.
        - Optional link functionality if `target_url` is provided.
        """

        # Create the row content for the button (text and optional icon)
        content = rio.Row(
            align_x=0.5,
            spacing=0.5,
            margin_x=self.margin_x_row,
            margin_y=self.margin_y_row,
        )

        # Add the button's text with custom styles
        content.add(
            rio.Text(
                self.text,
                font_size=self.font_size,
                font_weight=self.font_weight,
                fill=self.session.theme.primary_color,
            ),
        )

        # Add an icon to the button if specified
        if self.icon:
            content.add(
                rio.Icon(
                    self.icon,
                    fill=self.session.theme.primary_color,
                ),
            )

        # Wrap the content in a rectangle with outline and hover effects
        rectangle = rio.Rectangle(
            content=content,
            fill=self.session.theme.primary_color.replace(
                opacity=0.15
            ),  # Semi-transparent background
            transition_time=0.1,
            corner_radius=self.corner_radius,
            # Add stroke to create an outlined button
            stroke_width=0.1,
            stroke_color=self.session.theme.primary_color,
            # Change cursor to pointer on hover
            cursor="pointer",
        )

        # Return the rectangle as a button or a link if `target_url` is
        # specified
        if self.target_url is None:
            return rectangle
        else:
            return rio.Link(
                rectangle,
                target_url=self.target_url,
                open_in_new_tab=True,
            )


# </component>
