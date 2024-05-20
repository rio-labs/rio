import datetime
from dataclasses import dataclass

import rio


@dataclass
class TodoItem:
    title: str
    creation_time: datetime.datetime
    completed: bool = False


class TodoAppSettings(rio.UserSettings):
    todo_items: list[TodoItem] = []
