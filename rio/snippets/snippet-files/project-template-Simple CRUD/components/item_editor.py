import rio

# <additional-imports>
from .. import data_models

# </additional-imports>


# <component>
class ItemEditor(rio.Component):
    """
    A component for editing a menu item.

    Returns a card component containing the menu item editor. The editor
    contains fields for name, description, price, and category of the menu item.
    The component also contains buttons for saving or canceling the changes.

    The on_change methods are event handlers for the respective input fields.
    These methods update the attributes of the currently selected menu item.

    ## Attributes

    `currently_selected_menu_item`: The currently selected menu item.

    `new_entry`: A boolean flag indicating if the menu item is a new entry.

    `on_cancel_event`: An event handler for the cancel button.

    `on_save_event`: An event handler for the save button.
    """

    currently_selected_menu_item: data_models.MenuItem
    new_entry: bool = False
    on_cancel_event: rio.EventHandler[[]] = None
    on_save_event: rio.EventHandler[[]] = None

    def on_change_name(self, ev: rio.TextInputChangeEvent) -> None:
        """
        Changes the name of the currently selected menu item. And updates the
        name attribute of our data model.

        ## Parameters

        `ev`: The event object that contains the new name.
        """
        self.currently_selected_menu_item.name = ev.text

    def on_change_description(self, ev: rio.TextInputChangeEvent) -> None:
        """
        Changes the description of the currently selected menu item. And updates
        the description attribute of our data model.

        ## Parameters

        `ev`: The event object that contains the new description.
        """
        self.currently_selected_menu_item.description = ev.text

    def on_change_price(self, ev: rio.NumberInputChangeEvent) -> None:
        """
        Changes the price of the currently selected menu item. And updates the
        price attribute of our data model.

        ## Parameters
        `ev`: The event object that contains the new price.
        """
        self.currently_selected_menu_item.price = ev.value

    def on_change_category(self, ev: rio.DropdownChangeEvent) -> None:
        """
        Changes the category of the currently selected menu item. And updates
        the category attribute of our data model.

        ## Parameters
        `ev`: The event object that contains the new category.
        """
        self.currently_selected_menu_item.category = ev.value

    def build(self) -> rio.Component:
        """
        Builds the menu item editor component.

        See the approx. layout below:

        ```
        ╔══════════════════════ Card ══════════════════════╗
        ║ ┏━━━━━━━━━━━━━━━━━━━━ Text ━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ Edit Menu Item | Add New Menu Item           ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┏━━━━━━━━━━━━━━━━━━ TextInput ━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ Name                                         ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┏━━━━━━━━━━━━━━━━━━ TextInput ━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ Description                                  ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┏━━━━━━━━━━━━━━━━━ NumberInput ━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ Price                                        ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┏━━━━━━━━━━━━━━━━━━ Dropdown ━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃ Category                                     ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ║ ┏━━━━━━━━━━━━━━━━━━━━━ Row ━━━━━━━━━━━━━━━━━━━━┓ ║
        ║ ┃   ┏━━━ Button ━━━┓        ┏━━━ Button ━━━┓   ┃ ║
        ║ ┃   ┃ Save         ┃        ┃ Cancel       ┃   ┃ ║
        ║ ┃   ┗━━━━━━━━━━━━━━┛        ┗━━━━━━━━━━━━━━┛   ┃ ║
        ║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
        ╚══════════════════════════════════════════════════╝
        ```
        """

        if self.new_entry is False:
            text = "Edit Menu Item"
        else:
            text = "Add New Menu Item"

        return rio.Card(
            rio.Column(
                rio.Text(
                    text=text,
                    style="heading2",
                    margin_bottom=1,
                ),
                rio.TextInput(
                    self.currently_selected_menu_item.name,
                    label="Name",
                    on_change=self.on_change_name,
                ),
                rio.TextInput(
                    self.currently_selected_menu_item.description,
                    label="Description",
                    on_change=self.on_change_description,
                ),
                rio.NumberInput(
                    self.currently_selected_menu_item.price,
                    label="Price",
                    suffix_text="$",
                    on_change=self.on_change_price,
                ),
                rio.Dropdown(
                    options=[
                        "Burgers",
                        "Desserts",
                        "Drinks",
                        "Salads",
                        "Sides",
                    ],
                    label="Category",
                    selected_value=self.currently_selected_menu_item.category,
                    on_change=self.on_change_category,
                ),
                rio.Row(
                    rio.Button("Save", on_press=self.on_save_event),
                    rio.Button("Cancel", on_press=self.on_cancel_event),
                    spacing=1,
                    align_x=1,
                ),
                spacing=1,
                align_y=0,
                margin=2,
            ),
        )


# </component>
