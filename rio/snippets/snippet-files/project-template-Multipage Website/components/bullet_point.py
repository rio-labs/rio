import rio

# <additional-imports>
from .. import data_models, theme

# </additional-imports>


# <component>
class BulletPoint(rio.Component):
    """
    A component that displays a bullet point with an icon, title, and
    description.


    ## Attributes:

    `title`: The title text of the bullet point.

    `description`: The description text of the bullet point.

    `icon`: The icon displayed next to the bullet point.
    """

    title: str
    description: str
    icon: str

    def build(self) -> rio.Component:
        """
        Builds the bullet point component.

        This component consists of:
        - An icon aligned with the title and description.
        - A title with bold styling.
        - A description that adapts to the device layout for mobile and desktop.
        """
        device = self.session[data_models.PageLayout].device
        return rio.Row(
            rio.Icon(
                self.icon,
                fill="primary",
                min_height=1.5,
                min_width=1.5,
                align_y=0,
            ),
            rio.Column(
                # Title text of the bullet point
                rio.Text(
                    self.title,
                    style=theme.BOLD_BRIGHTER_TEXT,
                ),
                # Description text
                rio.Text(
                    self.description,
                    # Adapt text wrapping to device type
                    overflow="wrap" if device == "mobile" else "nowrap",
                    # Ensure minimum width for mobile devices
                    min_width=18 if device == "mobile" else 0,  # TODO
                ),
            ),
            spacing=1,
            margin_y=0.5,
            align_x=0,
        )


# </component>
