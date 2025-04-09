import rio

# <additional-imports>
from .. import components as comps
from .. import data_models, theme

# </additional-imports>


# <component>
class TableHeader(rio.Component):
    """
    Custom component to display the header of the table.

    The header consists of a row with the selected display options.
    """

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Row(
                rio.Checkbox(),
                rio.Text(
                    "#",
                    font_size=0.9,
                    font_weight="bold",
                ),
                rio.Text(
                    "Name",
                    font_size=0.9,
                    font_weight="bold",
                ),
                rio.Text(
                    "Email",
                    font_size=0.9,
                    font_weight="bold",
                ),
                rio.Text(
                    "Location",
                    font_size=0.9,
                    font_weight="bold",
                ),
                rio.Text(
                    "Status",
                    font_size=0.9,
                    font_weight="bold",
                ),
                margin_y=1,
                proportions=[0.4, 0.4, 1, 1, 1, 1],
            ),
            rio.Separator(color=self.session.theme.neutral_color),
        )


class TableRow(rio.Component):
    """
    Custom component to display a row of the table.

    The row consists of a checkbox and the user's ID, name, email, location, and
    status based on the selected display options.

    ## Attributes:

    `user`: The user object containing details such as ID, name, email,
    location, and status.
    """

    user: data_models.User

    def build(self) -> rio.Component:
        # Build the content of the row using the user data
        content = rio.Column(
            rio.Row(
                rio.Checkbox(),
                rio.Text(
                    str(self.user.id_number),
                    style=theme.TEXT_STYLE_DARKER_SMALL,
                ),
                rio.Row(
                    rio.Rectangle(
                        fill=rio.ImageFill(
                            self.session.assets / self.user.image
                        ),
                        corner_radius=999999,
                        align_x=0,
                        align_y=0.5,
                        min_height=1.5,
                        min_width=1.5,
                    ),
                    rio.Text(
                        self.user.name,
                        font_size=0.9,
                    ),
                    spacing=0.5,
                    align_x=0,
                ),
                rio.Text(
                    self.user.email,
                    style=theme.TEXT_STYLE_DARKER_SMALL,
                ),
                rio.Text(
                    self.user.location,
                    style=theme.TEXT_STYLE_DARKER_SMALL,
                ),
                comps.ColoredRectangle(content=self.user.status),
                margin_y=1,
                proportions=[0.4, 0.4, 1, 1, 1, 1],
            ),
            rio.Separator(color=self.session.theme.neutral_color),
        )

        return rio.Rectangle(
            content=content,
            fill=self.session.theme.background_color,
            hover_fill=self.session.theme.background_color.brighter(0.05),
            transition_time=0.1,
        )


class UserTable(rio.Component):
    """
    Custom component to display a table of users.

    The table consists of a header and multiple rows, each representing a user
    entry. Displaying the user's ID, name, email, location, and status based on
    the selected display options.


    ## Attributes:

    `users`: Each user is represented as a data_models.User instance.
    """

    users: list[data_models.User]

    def build(self) -> rio.Component:
        # Build the content of the table using the user data
        content = rio.Column()
        content.add(TableHeader())

        # Add a row for each user in the users list
        for user in self.users:
            content.add(
                TableRow(
                    user=user,
                )
            )

        return content


# </component>
