# import dataclasses

from dataclasses import field

import rio

# <additional-imports>
from .. import components as comps
from .. import constants, data_models

# </additional-imports>


# <component>
@rio.page(
    name="Users",
    url_segment="users",
)
class UserPage(rio.Component):
    """
    Custom component to display the users page.

    The page consists of a title, a filter row, and a user table. The user table
    displays the users based on the selected statuses and locations.


    ## Attributes:

    `users`: A list of users.

    `status_options`: A list of status options.

    `location_options`: A list of location options.

    `display_options`: A list of display options.
    """

    users: list[data_models.User] = field(
        default_factory=lambda: constants.USERS
    )

    status_options_selected: list[str] = field(
        default_factory=lambda: constants.STATUS_OPTIONS.copy()
    )
    location_options_selected: list[str] = field(
        default_factory=lambda: constants.LOCATION_OPTIONS.copy()
    )

    def on_change_status_options(
        self, ev: comps.MultiSelectDropdownChangeEvent
    ) -> None:
        """
        Change the selected status option.
        """
        # Update the selected options based on the event
        self.status_options_selected = ev.values

        # Force a refresh to update the UI
        self.force_refresh()

    def on_change_location_options(
        self, ev: comps.MultiSelectDropdownChangeEvent
    ) -> None:
        """
        Change the selected locations option.
        """
        # Update the selected options based on the event
        self.location_options_selected = ev.values

        # Force a refresh to update the UI
        self.force_refresh()

    def filter_users(self) -> list[data_models.User]:
        """
        Filter the users based on the selected statuses and locations.

        Normally, this would be done by querying a database, but for this
        example, we will filter the users in memory.
        """
        users_filtered = []

        # Filter the users based on the selected statuses and locations
        for user in self.users:
            if (
                user.status in self.status_options_selected
                and user.location in self.location_options_selected
            ):
                # if user.status in selected_statuses:
                users_filtered.append(user)

        return users_filtered

    def build(self) -> rio.Component:
        # Apply filters to users, then pass the filtered users to the UserTable
        # component.
        users_filtered = self.filter_users()

        return rio.Column(
            rio.Column(
                rio.Separator(
                    color=self.session.theme.neutral_color,
                    align_y=0,
                ),
                rio.Text(
                    "Users",
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
            comps.FilterRow(
                status_options={
                    item: item for item in constants.STATUS_OPTIONS
                },
                status_options_selected=self.status_options_selected,
                location_options={
                    item: item for item in constants.LOCATION_OPTIONS
                },
                location_options_selected=self.location_options_selected,
                on_change_status=self.on_change_status_options,
                on_change_location=self.on_change_location_options,
            ),
            rio.ScrollContainer(
                comps.UserTable(
                    users=users_filtered,
                    align_y=0,
                ),
                grow_y=True,
            ),
        )


# </component>
