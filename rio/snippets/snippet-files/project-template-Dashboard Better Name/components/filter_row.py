import rio

# <additional-imports>
from .. import components as comps

# </additional-imports>


# <component>
class FilterRow(rio.Component):
    """
    A component that represents a row of filters for selecting status and
    location options.

    This component provides dropdowns for filtering data based on status and
    location. It supports multi-select functionality and triggers events when
    the selected options change.


    ## Attributes

    `status_options`: A dictionary of available status options with their
    labels.

    `status_options_selected`: A list of currently selected status options.

    `location_options`: A dictionary of available location options with their
    labels.

    `location_options_selected`: A list of currently selected location options.

    `on_change_status`: An event handler triggered when the status selection
    changes.

    `on_change_location`: An event handler triggered when the location selection
    changes.
    """

    status_options: dict[str, str]
    status_options_selected: list[str]
    location_options: dict[str, str]
    location_options_selected: list[str]

    on_change_status: rio.EventHandler[
        comps.MultiSelectDropdownChangeEvent[str]
    ] = None
    on_change_location: rio.EventHandler[
        comps.MultiSelectDropdownChangeEvent[str]
    ] = None

    async def _on_change_status(
        self, selected_values: comps.MultiSelectDropdownChangeEvent[str]
    ) -> None:
        """
        Handles the change event for the status dropdown.
        """
        await self.call_event_handler(self.on_change_status, selected_values)

    async def _on_change_location(
        self, selected_values: comps.MultiSelectDropdownChangeEvent[str]
    ) -> None:
        """
        Handles the change event for the location dropdown.
        """
        await self.call_event_handler(self.on_change_location, selected_values)

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Row(
                comps.MultiSelectDropdown(
                    label="Status",
                    label_icon="material/check_circle",
                    options=self.status_options,
                    selected_values=self.status_options_selected,
                    on_change=self._on_change_status,
                ),
                comps.MultiSelectDropdown(
                    label="Location",
                    label_icon="material/location_on",
                    options=self.location_options,
                    selected_values=self.location_options_selected,
                    on_change=self._on_change_location,
                ),
                spacing=0.5,
                align_x=0,
                align_y=0.5,
                margin_x=1,
                margin_y=0.5,
            ),
            rio.Separator(
                color=self.session.theme.neutral_color,
                align_y=1,
            ),
            align_y=0,
        )


# </component>
