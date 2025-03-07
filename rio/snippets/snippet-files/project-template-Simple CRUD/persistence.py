from . import data_models


class Persistence:
    """
    A class to handle operations for the MenuItems.

    You can adapt this class to your needs by adding more methods to interact
    with the "database" or support different databases like SQLight or MongoDB.

    ## Attributes

    `menu_items`: The list of MenuItem objects.
    """

    def __init__(self) -> None:
        """
        Initializes the Persistence object with a list of MenuItem objects.
        """
        self.menu_items: list[data_models.MenuItem] = (
            self._populate_menu_items()
        )

    def _populate_menu_items(self) -> list[data_models.MenuItem]:
        """
        Populates the initial list of MenuItem objects.
        """
        return [
            data_models.MenuItem(
                name="Hamburger",
                description="A classic hamburger with lettuce, tomato, and onions",
                price=4.99,
                category="Burgers",
            ),
            data_models.MenuItem(
                name="Cheeseburger",
                description="A classic cheeseburger with lettuce, tomato, onions and cheese",
                price=5.99,
                category="Burgers",
            ),
            data_models.MenuItem(
                name="Fries",
                description="A side of crispy fries",
                price=2.99,
                category="Sides",
            ),
            data_models.MenuItem(
                name="Soda",
                description="A refreshing soda",
                price=1.99,
                category="Drinks",
            ),
            data_models.MenuItem(
                name="Salad",
                description="A fresh salad",
                price=4.99,
                category="Salads",
            ),
            data_models.MenuItem(
                name="Ice Cream",
                description="A sweet treat",
                price=3.99,
                category="Desserts",
            ),
        ]
