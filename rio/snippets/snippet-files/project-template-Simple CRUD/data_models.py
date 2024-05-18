from __future__ import annotations

from dataclasses import dataclass
from typing import *  # type:ignore


@dataclass
class MenuItem:
    """
    MenuItem data model.

    ## Attributes

    `name`: The name of the menu item.

    `description`: The description of the menu item.

    `price`: The price of the menu item.

    `category`: The category of the menu item.
    """

    name: str
    description: str
    price: float
    category: str

    @staticmethod
    def new_empty() -> MenuItem:
        """
        Creates a new empty MenuItem object.
        """
        return MenuItem(
            name="",
            description="",
            price=0.0,
            category="",
        )


# Initialize some data
MENU_ITEMS: list[MenuItem] = [
    MenuItem(
        name="Hamburger",
        description="A classic hamburger with lettuce, tomato, and onions",
        price=4.99,
        category="Burgers",
    ),
    MenuItem(
        name="Cheeseburger",
        description="A classic cheeseburger with lettuce, tomato, onions and cheese",
        price=5.99,
        category="Burgers",
    ),
    MenuItem(
        name="Fries",
        description="A side of crispy fries",
        price=2.99,
        category="Sides",
    ),
    MenuItem(
        name="Soda",
        description="A refreshing soda",
        price=1.99,
        category="Drinks",
    ),
    MenuItem(
        name="Salad",
        description="A fresh salad",
        price=4.99,
        category="Salads",
    ),
    MenuItem(
        name="Ice Cream",
        description="A sweet treat",
        price=3.99,
        category="Desserts",
    ),
]
