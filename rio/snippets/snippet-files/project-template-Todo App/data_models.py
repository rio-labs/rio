import dataclasses
import datetime

import rio


@dataclasses.dataclass
class TodoItem:
    title: str
    creation_time: datetime.datetime
    completed: bool = False


class TodoAppSettings(rio.UserSettings):
    todo_items: list[TodoItem] = []
