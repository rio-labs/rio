from __future__ import annotations

import copy
import dataclasses


@dataclasses.dataclass
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

    def copy(self) -> MenuItem:
        """
        Creates a copy of the MenuItem object.
        """
        return copy.copy(self)
