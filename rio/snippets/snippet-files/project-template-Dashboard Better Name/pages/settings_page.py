import rio

# <additional imports>
from .. import components as comps

# </additional imports>


# <component>
@rio.page(
    name="Settings",
    url_segment="settings",
)
class Settings(rio.Component):
    """
    Represents the Settings page of the application.

    This page provides a layout for displaying and managing various settings. It
    includes a header with a title, separators for visual structure, a section
    switcher for navigating between different settings sections, and a main
    content area for displaying the selected section's content.
    """

    @rio.event.on_page_change
    def on_page_change(self) -> None:
        self.force_refresh()

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Column(
                rio.Separator(
                    color=self.session.theme.neutral_color,
                    align_y=0,
                ),
                rio.Text(
                    "Settings",
                    font_size=1,
                    font_weight="bold",
                    align_x=0,
                    align_y=0.5,
                    margin_left=1,
                    grow_y=True,
                ),
                align_y=0,
                min_height=4,
            ),
            rio.Separator(color=self.session.theme.neutral_color, align_y=1),
            comps.SectionSwitcher(),
            rio.PageView(
                grow_x=True,
                grow_y=True,
                margin_x=1,
                margin_top=1.5,
            ),
        )


# </component>
