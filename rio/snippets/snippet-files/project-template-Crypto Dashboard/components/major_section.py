import rio

# <additional-imports>
from .. import data_models

# </additional-imports>


# <component>
class MajorSection(rio.Component):
    """
    Represents a major section in the sidebar.

    This component displays a clickable section with an icon and text. The
    appearance of the section changes based on whether it is active or inactive.


    ## Attributes:

    `main_section`: The data for the section, including its name and icon.

    `is_active`: Indicates if the section is currently active.
    """

    main_section: data_models.MainSection

    is_active: bool = False

    def build(self) -> rio.Component:
        # Determine styles and fills based on the active state
        if self.is_active:
            fill = self.session.theme.neutral_color
            hover_fill = self.session.theme.neutral_color
            font_weight = "bold"
            icon_fill = ":fill"

        else:
            fill = rio.Color.TRANSPARENT
            hover_fill = self.session.theme.neutral_color.darker(0.1)
            font_weight = "normal"
            icon_fill = ""

        return rio.Rectangle(
            content=rio.Row(
                # Add the icon with conditional filling
                rio.Icon(f"{self.main_section.icon}{icon_fill}"),
                # Add the section name with appropriate text styling
                rio.Text(
                    self.main_section.main_section_name,
                    font_weight=font_weight,
                    selectable=False,
                ),
                spacing=0.5,
                margin=1,
                align_x=0,
            ),
            fill=fill,
            hover_fill=hover_fill,
            cursor="pointer",
            transition_time=0.1,
            corner_radius=self.session.theme.corner_radius_medium,
        )


# </component>
