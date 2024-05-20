# Simple CRUD

This template shows off a simple CRUD App, which allows you to create,
read, update, and delete menu items.

## Lessons

In this example you can see:

-   How to populate your application with your own data, add new items, edit
    existing items, and delete items. The data is stored in the `menu_items`
    state of the `CrudPage` component.
-   How to pass data between components and how to trigger actions in one
    component from another using rio's `EventHandler`.

## Components

The example is composed of three main components:

1. `ItemList`: Displays the list of menu items and allows the user to add new
   items, delete existing items, or select an item for editing.
2. `ItemEditor`: Allows the user to edit the details of a selected menu item or
   create a new item.
3. `CrudPage`: Combines the `ItemList` and `ItemEditor` component and adds some
   logic.
