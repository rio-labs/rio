import rio

# <additional-imports>
from .. import components as comps
from .. import constants

# </additional-imports>


# <component>
class SectionSwitcher(rio.Component):
    """
    A component that provides a navigation bar for switching between different
    sections of the settings page.

    Displays buttons for navigating to the "General", "Members", and
    "Notifications" sections. It also includes a link to the documentation.
    """

    @rio.event.on_page_change
    def on_page_change(self) -> None:
        """
        Triggered whenever the session changes pages.
        """
        self.force_refresh()

    def build(self) -> rio.Component:
        active_url = self.session.active_page_url.path

        # Get Settings sections from MAJOR_SECTIONS
        settings_sections = next(
            (
                section.sections
                for section in constants.MAJOR_SECTIONS
                if section.main_section_name == "Settings"
            ),
            [],
        )

        # Create a SelectorButton for each section
        section_buttons = []
        for section in settings_sections:
            section_buttons.append(
                comps.SelectorButton(
                    section=section.section_name,
                    section_icon=section.icon,
                    section_url_fragment=section.target_url,
                    is_active=True
                    if active_url == section.target_url
                    else False,
                )
            )

        content = rio.Row(
            # Unpack the list of section buttons
            *section_buttons,
            rio.Spacer(),
            rio.Link(
                comps.HoverCard("Documentation", "material/import_contacts"),
                target_url="https://rio.dev/docs",
                open_in_new_tab=True,
            ),
            spacing=1,
            align_y=0.5,
            margin_x=1,
        )

        return rio.Column(
            content,
            rio.Separator(
                color=self.session.theme.neutral_color,
                align_y=0,
            ),
            min_height=3.5,
        )


# </component>
