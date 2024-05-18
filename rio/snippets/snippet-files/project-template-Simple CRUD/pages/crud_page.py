from typing import *  # type:ignore

import rio

# <additional-imports>
from .. import components as comps
from .. import data_models

# </additional-imports>


# <component>
class CrudPage(rio.Component):
    """
    A CRUD page that allows users to create, read, update, and delete menu
    items.

    This component is composed of a Banner component, an ItemList component, and
    an ItemEditor component.

    The @rio.event.on_populate decorator is used to fetch data from a predefined
    data model and assign it to the menu_items attribute of the current
    instance. The on_press_delete_item, on_press_cancel_event, and
    on_press_save_event methods are used to handle delete, cancel, and save
    events, respectively. The on_press_add_new_item method is used to handle the
    add new item event. The on_press_select_menu_item method is used to handle
    the selection of a menu item.

    ## Attributes

    `menu_items`: A list of menu items.

    `currently_selected_menu_item`: The currently selected menu item.

    `banner_text`: The text to be displayed in the banner.

    `banner_style`: The style of the banner (success, danger, info).

    `is_new_entry`: A flag to indicate if the currently selected menu item is a
        new entry.
    """

    menu_items: list[data_models.MenuItem] = []
    currently_selected_menu_item: data_models.MenuItem | None = None
    banner_text: str = ""
    banner_style: Literal["success", "danger", "info"] = "success"
    is_new_entry: bool = False

    @rio.event.on_populate
    def on_populate(self) -> None:
        """
        Event handler that is called when the component is populated.

        Fetches data from a predefined data model and assigns it to the menu_items
        attribute of the current instance.
        """
        self.menu_items = data_models.MENU_ITEMS

    async def on_press_delete_item(self, idx: int) -> None:
        """
        Perform actions when the "Delete" button is pressed.

        ## Parameters

        `idx`: The index of the item to be deleted.
        """
        # delete the item from the list
        self.menu_items.pop(idx)
        self.banner_text = "Item was deleted"
        self.banner_style = "danger"
        self.currently_selected_menu_item = None

    async def on_press_cancel_event(self) -> None:
        """
        Perform actions when the "Cancel" button is pressed.
        """
        self.currently_selected_menu_item = None
        self.banner_text = ""

    def on_press_save_event(self) -> None:
        """
        Performs actions when the "Save" button is pressed.

        This method appends the currently selected menu item to the menu item
        set if it is a new entry, or updates the menu item set if it is an
        existing entry. It also updates the banner text and sets the
        is_new_entry flag to False.
        """
        assert self.currently_selected_menu_item is not None

        if self.is_new_entry:
            self.menu_items.append(self.currently_selected_menu_item)
            self.banner_text = "Item was added"
            self.banner_style = "success"
            self.is_new_entry = False
            self.currently_selected_menu_item = None
        else:
            self.banner_text = "Item was updated"
            self.banner_style = "info"

    async def on_press_add_new_item(self) -> None:
        """
        Perform actions when the "Add New" ListItem is pressed.

        This method sets the currently selected menu item to a new empty
        instance of models.MenuItems, clears the banner text, and sets the
        is_new_entry flag to True.
        """
        self.currently_selected_menu_item = data_models.MenuItem.new_empty()
        self.banner_text = ""
        self.is_new_entry = True

    async def on_press_select_menu_item(
        self, selected_menu_item: data_models.MenuItem
    ) -> None:
        """
        Perform actions when a menu item is selected.

        This method sets the currently selected menu item to the selected menu
        item, which is passed as an argument.

        ## Parameters

        `selected_menu_item`: The selected menu item.
        """
        self.currently_selected_menu_item = selected_menu_item

    def build(self) -> rio.Component:
        """
        Builds the component to be rendered.

        If there is no currently selected menu item, only the Banner and
        ItemList component is returned.

        Otherwise, if there is a currently selected menu item, both the Banner
        and ItemList component and the ItemEditor component are returned.

        See the approx. layout below:

        ```
        ╔══════════════════════ Card ═══════════════════════╗
        ║ ┏━━━━━━━━━━━━━━━━━━━ Banner ━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ "" | Item was updated | Item was added        ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┏━━━━━━━━━━━━━━━━━━ ItemList ━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ our custom component                          ┃ ║
        ║ ┃                                               ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ╚═══════════════════════════════════════════════════╝
        ```
        or
        ```
        ╔══════════════════════ Card ═══════════════════════╗
        ║ ┏━━━━━━━━━━━━━━━━━━━ Banner ━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ "" | Item was updated | Item was added        ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┏━━━━━━ ItemList ━━━━━━┓ ┏━━━━━ ItemEditor ━━━━━┓ ║
        ║ ┃ our custom component ┃ ┃ our custom component ┃ ║
        ║ ┃                      ┃ ┃                      ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━┛ ┗━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ╚═══════════════════════════════════════════════════╝
        ```
        """

        if self.currently_selected_menu_item is None:
            return rio.Column(
                rio.Banner(self.banner_text, style=self.banner_style),
                comps.ItemList(
                    menu_items=self.menu_items,
                    on_add_new_item_event=self.on_press_add_new_item,
                    on_delete_item_event=self.on_press_delete_item,
                    on_select_item_event=self.on_press_select_menu_item,
                    align_y=0,
                ),
                align_y=0,
                margin=3,
            )
        else:
            return rio.Column(
                rio.Banner(self.banner_text, style=self.banner_style),
                rio.Row(
                    comps.ItemList(
                        menu_items=self.menu_items,
                        on_add_new_item_event=self.on_press_add_new_item,
                        on_delete_item_event=self.on_press_delete_item,
                        on_select_item_event=self.on_press_select_menu_item,
                        align_y=0,
                    ),
                    comps.ItemEditor(
                        self.currently_selected_menu_item,
                        new_entry=self.is_new_entry,
                        on_cancel_event=self.on_press_cancel_event,
                        on_save_event=self.on_press_save_event,
                    ),
                    spacing=1,
                    proportions=(1, 1),
                ),
                spacing=1,
                align_y=0,
                margin=3,
            )


# </component>
