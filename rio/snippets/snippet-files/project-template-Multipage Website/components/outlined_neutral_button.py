# <additional-imports>
import rio

from .. import theme

# </additional-imports>


# <component>
class OutlinedNeutralButton(rio.Component):
    """
    A button component with an outlined neutral style.


    ## Attributes:

    `text`: The label to display on the button.

    `icon`: Optional icon to display alongside the button text.
    """

    text: str
    icon: str | None = None

    def build(self) -> rio.Component:
        """
        Builds the outlined neutral button component.
        """
        # Create the content for the button (text and optional icon)
        content = rio.Row(
            rio.Text(self.text),
            align_x=0.5,  # Center the text horizontally
            spacing=1,  # Add spacing between elements (used if icon is added)
            margin_x=1,  # Add horizontal margin
            margin_y=0.5,  # Add vertical margin
        )

        # Add an icon to the content if specified
        if self.icon:
            content.add(
                rio.Icon(
                    self.icon,
                    min_height=1.5,
                    min_width=1.5,
                ),
            )

        # Wrap the content in a rectangle to provide styling and interactivity
        return rio.Rectangle(
            content=content,
            fill=self.session.theme.neutral_color,
            hover_fill=self.session.theme.neutral_color.brighter(0.05),
            transition_time=0.1,  # Smooth transition for hover effects
            corner_radius=9999,  # Fully rounded corners
            # Add stroke to create an outlined button
            stroke_width=0.1,
            stroke_color=theme.NEUTRAL_COLOR_BRIGHTER,
            cursor="pointer",  # Change cursor to pointer on hover
        )


# </component>
