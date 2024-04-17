from dataclasses import dataclass
from typing import *  # type:ignore


@dataclass
class MenuItems:
    """
    MenuItems data model.

    ## Attributes
        name: The name of the menu item.
        description: The description of the menu item.
        price: The price of the menu item.
        category: The category of the menu item.
    """

    name: str
    description: str
    price: float
    category: str

    @staticmethod
    def new_empty() -> "MenuItems":
        """
        Creates a new empty MenuItems object.

        Returns:
            MenuItems: A new empty MenuItems object.
        """
        return MenuItems(
            name="",
            description="",
            price=0.0,
            category="",
        )


# initial data
MENUITEMSET: list[MenuItems] = [
    MenuItems(
        name="Hamburger",
        description="A classic hamburger with lettuce, tomato, and onions",
        price=4.99,
        category="Burgers",
    ),
    MenuItems(
        name="Cheeseburger",
        description="A classic cheeseburger with lettuce, tomato, onions and cheese",
        price=5.99,
        category="Burgers",
    ),
    MenuItems(
        name="Fries",
        description="A side of crispy fries",
        price=2.99,
        category="Sides",
    ),
    MenuItems(
        name="Soda",
        description="A refreshing soda",
        price=1.99,
        category="Drinks",
    ),
    MenuItems(
        name="Salad",
        description="A fresh salad",
        price=4.99,
        category="Salads",
    ),
    MenuItems(
        name="Ice Cream",
        description="A sweet treat",
        price=3.99,
        category="Desserts",
    ),
]
