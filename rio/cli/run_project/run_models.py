import dataclasses
from pathlib import Path


class Event:
    pass


@dataclasses.dataclass
class FileChanged(Event):
    """
    A file in the project has changed, necessitating a reload.
    """

    timestamp_nanoseconds: (
        int  # Monotonic timestamp of the change, in nanoseconds
    )
    path_to_file: Path


@dataclasses.dataclass
class StopRequested(Event):
    """
    Request a shutdown of the running project.
    """

    pass
