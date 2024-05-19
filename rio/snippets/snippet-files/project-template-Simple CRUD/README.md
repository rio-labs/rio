This template shows off a simple CRUD App, which allows you to create, read,
update, and delete menu items.

In this example you will learn how to populate your application with your own
data, add new items, edit existing items, and delete items. The data is stored
in the `menu_items` state of the `CrudPage` component. In addition, you will see
how to pass data between components and how to trigger actions in one component
from another using `EventHandler`s.

## Main Components

The example is composed of three main components:

1. ItemList: Displays the list of menu items and allows the user to add new
   items, delete existing items, or select an item for editing.
1. ItemEditor: Allows the user to edit the details of a selected menu item or
   create a new item.
1. CrudPage: Combines the ItemList and ItemEditor component and add some logic.
