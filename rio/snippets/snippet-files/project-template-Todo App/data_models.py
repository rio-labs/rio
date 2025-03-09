import dataclasses
import datetime

import rio


@dataclasses.dataclass
class TodoItem:
    title: str
    creation_time: datetime.datetime
    completed: bool = False


class TodoAppSettings(rio.UserSettings):
    todo_items: list[TodoItem] = [
        TodoItem(
            title="Wake up (optional, but highly recommended)",
            creation_time=datetime.datetime.now(),
        ),
        TodoItem(
            title="Convince myself I'm a morning person (fake it till I make it)",
            creation_time=datetime.datetime.now(),
        ),
        TodoItem(
            title="Drink coffee (or legally change my name to 'Zombie #1')",
            creation_time=datetime.datetime.now(),
        ),
        TodoItem(
            title="Attempt to be productive (a.k.a. stare at my to-do list and panic)",
            creation_time=datetime.datetime.now(),
        ),
        TodoItem(
            title="Eat something healthy (or at least something that once looked at a vegetable)",
            creation_time=datetime.datetime.now(),
        ),
        TodoItem(
            title="Pretend to work while actually just Googling random facts (Did you know octopuses have three hearts?)",
            creation_time=datetime.datetime.now(),
        ),
    ]
