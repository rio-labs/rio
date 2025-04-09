import rio

from .. import components as comps
from .. import data_models, theme

# class StyledRectangle(rio.Component):
#     """
#     A custom component to display a rectangle with text and an icon.

#     The option can be selected and deselected.


#     ## Attributes:

#     `name`: The name of the option.

#     `is_selected`: A boolean indicating whether the option is selected.

#     `on_press`: An event handler that is called when the option is pressed.
#     """

#     name: str
#     is_selected: bool = False

#     on_press: rio.EventHandler[[]] = None

#     async def _on_press(self, _: rio.PointerEvent) -> None:
#         await self.call_event_handler(self.on_press)

#     def build(self) -> rio.Component:

#         content = rio.Row(margin=0.5, spacing=0.5, min_height=1.2)

#         content.add(
#             rio.Text(
#                 self.name,
#                 selectable=False,
#                 style=rio.TextStyle(font_weight="bold", font_size=0.9),
#             ),
#         )
#         if self.is_selected:
#             content.add(rio.Spacer())
#             content.add(
#                 rio.Icon(
#                     "material/check",
#                     fill=self.session.theme.primary_color,
#                     align_y=0.5,
#                     min_width=1.2,
#                     min_height=1.2,
#                 ),
#             )

#         return rio.PointerEventListener(
#             rio.Rectangle(
#                 content=content,
#                 fill=rio.Color.TRANSPARENT,
#                 hover_fill=self.session.theme.background_color,
#                 corner_radius=self.session.theme.corner_radius_small,
#                 transition_time=0.1,
#                 cursor="pointer",
#             ),
#             on_press=self._on_press,
#         )


# class PopupRectangle(rio.Component):
#     options: list[data_models.Option]

#     on_change_option: rio.EventHandler[[data_models.Option]] = None

#     def on_press(self, _: rio.PointerEvent) -> None:
#         pass

#     async def _on_change_option(self, option: data_models.Option) -> None:
#         await self.call_event_handler(self.on_change_option, option)
#         self.force_refresh()  # TODO: check if needed

#     def build(self) -> rio.Component:
#         content = rio.Column(margin=0.5, spacing=0.5)

#         for option in self.options:
#             content.add(
#                 StyledRectangle(
#                     name=option.name,
#                     is_selected=option.is_selected,
#                     on_press=functools.partial(self._on_change_option, option),
#                 ),
#             )

#         # Styling the popup
#         return rio.PointerEventListener(
#             rio.Rectangle(
#                 content=content,
#                 fill=self.session.theme.neutral_color,
#                 stroke_width=0.1,
#                 stroke_color=self.session.theme.neutral_color.brighter(0.2),
#                 corner_radius=self.session.theme.corner_radius_small,
#                 transition_time=0.1,
#                 align_x=0.5,
#                 min_width=7.5,
#             ),
#             on_press=self.on_press,
#         )


# class Filter(rio.Component):
#     text: str
#     icon: str
#     popup_content: list[data_models.Option]
#     text_fill: rio.Color = rio.Color.GRAY.darker(0.1)
#     is_open: bool = False

#     on_change_option: rio.EventHandler[[data_models.Option]] = None

#     async def _on_change_option(self, option: data_models.Option) -> None:
#         await self.call_event_handler(self.on_change_option, option)

#     def on_press(self, _: rio.PointerEvent) -> None:
#         self.is_open = not self.is_open

#     def build(self) -> rio.Component:
#         return rio.Popup(
#             anchor=rio.PointerEventListener(
#                 rio.Rectangle(
#                     content=rio.Row(
#                         rio.Icon(
#                             self.icon,
#                             fill=rio.Color.GRAY.darker(0.1),
#                             align_y=0.5,
#                             min_width=1.2,
#                             min_height=1.2,
#                         ),
#                         rio.Text(
#                             self.text,
#                             selectable=False,
#                             style=rio.TextStyle(
#                                 fill=self.text_fill,
#                                 font_size=0.9,
#                             ),
#                         ),
#                         rio.Icon(
#                             "material/keyboard_arrow_down",
#                             fill=rio.Color.GRAY.darker(0.1),
#                             align_y=0.5,
#                         ),
#                         spacing=0.5,
#                         margin_x=0.5,
#                         margin_y=0.2,
#                         align_x=0,
#                         align_y=0.5,
#                     ),
#                     fill=self.session.theme.background_color,
#                     stroke_color=rio.Color.GRAY.darker(0.1),
#                     hover_stroke_color=self.session.theme.primary_color,
#                     stroke_width=0.1,
#                     corner_radius=self.session.theme.corner_radius_small,
#                 ),
#                 on_press=self.on_press,
#             ),
#             content=PopupRectangle(
#                 self.popup_content, on_change_option=self._on_change_option
#             ),
#             is_open=self.is_open,
#             position="bottom",
#             user_closable=True,
#         )


class FilterRow(rio.Component):
    status_options: dict[str, str]
    location_options: dict[str, str]
    display_options: dict[str, str]
    status_options_selected: list[str]
    location_options_selected: list[str]
    display_options_selected: list[str]

    on_change_display_options_selected: rio.EventHandler[[list[str]]] = None

    async def _on_change_display_options_selected(
        self, ev: comps.MultiSelectDropdownChangeEventMapping
    ) -> None:
        await self.call_event_handler(
            self.on_change_display_options_selected, ev.values
        )

    # async def on_change_option(self, option: data_models.Option) -> None:
    #     await self.call_event_handler(self.on_change_status, option)

    # def on_change_status(self, ev: comps.MultiSelectDropdownChangeEvent) -> None:
    #     print(f"FILTER ROW: status selected: {ev.values}")
    #     self.status_options_selected = ev.values

    #     self.force_refresh()

    # async def _on_change_display_options_selected(
    #     # self, event: comps.MultiSelectDropdownChangeEvent[list[str]]
    #     self,
    #     event: comps.MultiSelectDropdownChangeEvent,
    # ) -> None:
    #     # Access the selected values from the event object
    #     # selected_values = event.values
    #     await self.call_event_handler(
    #         self.on_change_display_options_selected, event.values
    #     )
    #     self.force_refresh()

    # async def on_change_status(self, ev: comps.MultiSelectDropdownChangeEvent) -> None:
    #     print(f"FILTER ROW: status selected!!!!: {ev.values}")
    #     self.status_options_selected = ev.values
    #     self.force_refresh()
    #     print("PRINT!!!!!!!!")

    def build(self) -> rio.Component:
        print(f"FILTER ROW: display selected: {self.display_options_selected}")
        print(f"FILTER ROW: status selected: {self.status_options_selected}")
        return rio.Column(
            rio.Row(
                comps.MultiSelectDropdownMapping(
                    label="Status",
                    label_icon="material/check_circle",
                    options=self.status_options,
                    selected_values=self.bind().status_options_selected,
                    # on_change=self.on_change_status,
                ),
                comps.MultiSelectDropdownMapping(
                    label="Location",
                    label_icon="material/location_on",
                    options=self.location_options,
                    selected_values=self.bind().location_options_selected,
                ),
                rio.Spacer(),
                comps.MultiSelectDropdownMapping(
                    label="Display",
                    label_icon="material/tune",
                    options=self.display_options,
                    selected_values=self.display_options_selected,
                    on_change=self._on_change_display_options_selected,
                ),
                spacing=0.5,
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


class TableHeader(rio.Component):
    """
    Custom component to display the header of the table.

    The header consists of a row with the selected display options.


    ## Attributes:

    `selected_display_options`: A list of strings representing the selected
    display options.
    """

    selected_display_options: list[str]

    def build(self) -> rio.Component:
        # Build the row based on the selected display options
        content_row = rio.Row(margin_y=1)
        content_row_proportions = [0.4]

        content_row.add(rio.Checkbox())

        if "#" in self.selected_display_options:
            content_row.add(
                rio.Text(
                    "#",
                    font_size=0.9,
                    font_weight="bold",
                ),
            )
            content_row_proportions.append(0.4)

        if "Name" in self.selected_display_options:
            content_row.add(
                rio.Text(
                    "Name",
                    font_size=0.9,
                    font_weight="bold",
                ),
            )
            content_row_proportions.append(1)

        if "Email" in self.selected_display_options:
            content_row.add(
                rio.Text(
                    "Email",
                    font_size=0.9,
                    font_weight="bold",
                ),
            )
            content_row_proportions.append(1)

        if "Location" in self.selected_display_options:
            content_row.add(
                rio.Text(
                    "Location",
                    font_size=0.9,
                    font_weight="bold",
                ),
            )
            content_row_proportions.append(1)

        if "Status" in self.selected_display_options:
            content_row.add(
                rio.Text(
                    "Status",
                    font_size=0.9,
                    font_weight="bold",
                ),
            )
            content_row_proportions.append(1)

        content_row.proportions = content_row_proportions

        return rio.Column(
            content_row,
            rio.Separator(color=self.session.theme.neutral_color),
        )


class TableRow(rio.Component):
    """
    Custom component to display a row of the table.

    The row consists of a checkbox and the user's ID, name, email, location, and
    status based on the selected display options.

    ## Attributes:

    `user`: The user is represented as a data_models.User instance.

    `selected_display_options`: A list of strings representing the selected
    display options.
    """

    user: data_models.User
    selected_display_options: list[str]

    def build(self) -> rio.Component:
        # Build the row based on the selected display options
        content_row = rio.Row(margin_y=1)
        content_row_proportions = [0.4]

        content_row.add(rio.Checkbox())

        if "#" in self.selected_display_options:
            content_row.add(
                rio.Text(
                    str(self.user.id_number),
                    style=theme.TEXT_STYLE_DARKER_SMALL,
                ),
            )
            content_row_proportions.append(0.4)

        if "Name" in self.selected_display_options:
            content_row.add(
                rio.Row(
                    rio.Rectangle(
                        fill=rio.ImageFill(
                            self.session.assets / self.user.image
                        ),
                        corner_radius=9999,
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
            )
            content_row_proportions.append(1)

        if "Email" in self.selected_display_options:
            content_row.add(
                rio.Text(
                    self.user.email,
                    style=theme.TEXT_STYLE_DARKER_SMALL,
                )
            )
            content_row_proportions.append(1)

        if "Location" in self.selected_display_options:
            content_row.add(
                rio.Text(
                    self.user.location,
                    style=theme.TEXT_STYLE_DARKER_SMALL,
                ),
            )
            content_row_proportions.append(1)

        if "Status" in self.selected_display_options:
            content_row.add(
                comps.ColoredRectangle(
                    content=self.user.status,
                    color=self.session.theme.success_color,
                ),
            )
            content_row_proportions.append(1)

        content_row.proportions = content_row_proportions

        return rio.Rectangle(
            content=rio.Column(
                content_row,
                rio.Separator(color=self.session.theme.neutral_color),
            ),
            fill=self.session.theme.background_color,
            hover_fill=self.session.theme.background_color.brighter(
                0.05
            ),  # TODO: make this hover_fill color for all components
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

    `display_options`: A list of data_models.Option instances representing the
    selected display options.
    """

    users: list[data_models.User]
    # users_filtered: list[data_models.User]

    status_options: dict[str, str]
    location_options: dict[str, str]
    display_options: dict[str, str]

    # selected_display_options: list[str] = []
    status_options_selected: list[str]
    location_options_selected: list[str]
    display_options_selected: list[str]

    cccccccc: list[str] = ["#", "Name", "Email", "Location", "Status"]

    # async def _on_change_display_options_selected(self, options: list[str]) -> None:
    #     self.display_options_selected = options
    #     self.force_refresh()

    # def on_change_status(self, option: list[str]) -> None:
    #     """
    #     Change the selection of the option.
    #     """
    #     option.is_selected = not option.is_selected
    #     self.force_refresh()

    def on_change_displayed_options_selected(self, options: list[str]) -> None:
        """
        Get the selected display options.
        """
        print(f"UserTable: selected display options before: {self.cccccccc}")
        print(f"UserTable: selected display options after: {options}")
        self.cccccccc = options
        self.display_options_selected = options

        print("CHANGED!!!!!!!!")
        print(f"UserTable: selected display options AFTER!!!: {self.cccccccc}")
        # self.display_options_selected = options
        self.force_refresh()

    def filter_users(self) -> list[data_models.User]:
        """
        Filter the users based on the selected statuses and locations.

        Normally, this would be done by querying a database, but for this
        example, we will filter the users in memory.
        """
        users_filtered = []

        # Get the selected statuses and locations
        selected_statuses = self.status_options_selected
        selected_locations = self.location_options_selected

        # Filter the users based on the selected statuses and locations
        for user in self.users:
            if (
                user.status in selected_statuses
                and user.location in selected_locations
            ):
                users_filtered.append(user)

        # return users_filtered
        # self.users_filtered = users_filtered
        # self.force_refresh()
        # self.force_refresh()
        return users_filtered

    def build(self) -> rio.Component:
        print(self.display_options_selected)

        users_filtered = self.filter_users()
        # selected_display_options = self.get_selected_display_options()
        # selected_display_options = self.display_options_selected
        table_content = rio.Column()
        table_content.add(
            # TableHeader(selected_display_options=self.bind().display_options_selected)
            TableHeader(selected_display_options=self.cccccccc)
            # TableHeader(selected_display_options=self.display_options_selected)
        )

        for user in self.users:
            table_content.add(
                TableRow(
                    user=user,
                    # selected_display_options=self.bind().display_options_selected,
                    selected_display_options=self.cccccccc,
                    # selected_display_options=self.display_options_selected,
                )
            )

        return rio.Column(
            FilterRow(
                self.status_options,
                self.location_options,
                self.display_options,
                status_options_selected=self.bind().status_options_selected,
                location_options_selected=self.bind().location_options_selected,
                display_options_selected=self.bind().display_options_selected,
                on_change_display_options_selected=self.on_change_displayed_options_selected,
            ),
            rio.ScrollContainer(
                table_content,
                grow_y=True,
            ),
        )


# class Table(rio.Component):
#     users: list[data_models.User]
#     selected_display_options: list[str]

#     def build(self) -> rio.Component:
#         table_content = rio.Column()
#         table_content.add(
#             TableHeader(selected_display_options=self.selected_display_options)
#         )

#         for user in self.users:
#             table_content.add(
#                 TableRow(
#                     user=user,
#                     selected_display_options=self.selected_display_options,
#                 )
#             )

#         return table_content
