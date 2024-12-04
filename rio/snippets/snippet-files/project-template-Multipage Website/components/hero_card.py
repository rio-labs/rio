# <additional-imports>
import rio

from .. import data_models, theme

# </additional-imports>


# <component>
class HeroCard(rio.Component):
    """
    A responsive card component that displays an icon, header, description, and
    interactive styling.


    ## Attributes:

    `icon`: The icon to display at the top of the card.

    `header`: The main title or header of the card.

    `description`: A brief description or body text for the card.
    """

    icon: str
    header: str
    description: str

    def build(self) -> rio.Component:
        """
        Builds the HeroCard component with responsive design and hover effects.

        The card includes:
        - An icon at the top.
        - A header text styled with bold emphasis.
        - A description that adjusts its width based on the device type.
        - Hover effects with color and border changes.
        """
        # Get the user's device type
        device = self.session[data_models.PageLayout].device
        return rio.Rectangle(
            content=rio.Column(
                # Add icon, header, and description
                rio.Icon(
                    self.icon,
                    fill="primary",
                    min_height=2.2,
                    min_width=2.2,
                    align_x=0,
                ),
                rio.Text(
                    self.header,
                    style=theme.BOLD_BRIGHTER_TEXT,
                ),
                rio.Text(
                    self.description,
                    overflow="wrap",
                    # Change min_width depending on device
                    min_width=15 if device == "mobile" else 20,
                ),
                spacing=1,
                margin=2,
                align_x=0,
            ),
            fill=rio.Color.TRANSPARENT,
            corner_radius=self.session.theme.corner_radius_medium,
            # Add border styling
            stroke_width=0.1,
            stroke_color=theme.NEUTRAL_COLOR_BRIGHTER,
            # Add hover effects
            hover_fill=self.session.theme.primary_color.replace(opacity=0.15),
            hover_stroke_color=self.session.theme.primary_color,
            transition_time=0.5,
        )


# </component>
