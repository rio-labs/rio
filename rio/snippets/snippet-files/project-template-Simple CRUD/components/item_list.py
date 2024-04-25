# <additional-imports>
import functools

import rio

from .. import data_models

# </additional-imports>


# <component>
class ItemList(rio.Component):
    """
    A component for displaying a list of menu items.

    Returns a list of menu items in a ListView component. Each item in the list contains the name,
    description, and a delete button. The delete button triggers an event to delete the item.

    ## Attributes
        menu_item_set: The list of menu items to be displayed.
        on_add_new_item_event: An event handler for adding a new item.
        on_delete_item_event: An event handler for deleting an item.
        on_select_item_event: An event handler for selecting an item.
    """

    menu_item_set: list[data_models.MenuItems]
    on_add_new_item_event: rio.EventHandler[[]] = None
    on_delete_item_event: rio.EventHandler[int] = None
    on_select_item_event: rio.EventHandler[data_models.MenuItems] = None

    async def on_press_add_new_item_event(self) -> None:
        """
        Asynchronously triggers the 'add new item' when the list item is pressed.
        """
        await self.call_event_handler(self.on_add_new_item_event)

    async def on_press_delete_item_event(self, idx: int) -> None:
        """
        Asynchronously triggers the 'delete item' when the delete button is pressed.
        The event handler is passed the index of the item to be deleted.

        ## Parameters
            idx: The index of the item to be deleted.
        """
        await self.call_event_handler(self.on_delete_item_event, idx)
        # update the list
        await self.force_refresh()

    async def on_press_select_item_event(
        self, item: data_models.MenuItems
    ) -> None:
        """
        Asynchronously triggers the 'select item' when an item is selected.
        The event handler is passed the selected item.

        ## Parameters
            item: The selected item.
        """
        await self.call_event_handler(self.on_select_item_event, item)

    def build(self) -> rio.Component:
        """
        Builds the component by returning a ListView component containing the menu items.

        Returns:
            A ListView component containing the menu items.
            See the approx. layout below:

        ############### ListView ###############
        #  + Add new                           #
        #  Hamburger          Button(Delete)   #
        #  Cheese Burger      Button(Delete)   #
        #  Fries              Button(Delete)   #
        #  ...                                 #
        ########################################
        """

        # Store all children in an intermediate list
        list_items = []

        list_items.append(
            rio.SimpleListItem(
                text="Add new",
                secondary_text="Description",
                key="add_new",
                left_child=rio.Icon("material/add"),
                on_press=self.on_press_add_new_item_event,
            )
        )

        for i, item in enumerate(self.menu_item_set):
            list_items.append(
                rio.SimpleListItem(
                    text=item.name,
                    secondary_text=item.description,
                    right_child=rio.Button(
                        rio.Icon("material/delete"),
                        color=self.session.theme.danger_color,
                        # Note the use of functools.partial to pass the
                        # index to the event handler.
                        on_press=functools.partial(
                            self.on_press_delete_item_event, i
                        ),
                    ),
                    # Use the name as the key to ensure that the list item
                    # is unique.
                    key=item.name,
                    # Note the use of functools.partial to pass the
                    # item to the event handler.
                    on_press=functools.partial(
                        self.on_press_select_item_event, item
                    ),
                )
            )

        # Then unpack the list to pass the children to the ListView
        return rio.ListView(
            *list_items,
            align_y=0,
        )


# </component>
