from dataclasses import dataclass
from pathlib import Path


class Event:
    pass


@dataclass
class FileChanged(Event):
    """
    A file in the project has changed, necessitating a reload.
    """

    timestamp_nanoseconds: (
        int  # Monotonic timestamp of the change, in nanoseconds
    )
    path_to_file: Path


@dataclass
class StopRequested(Event):
    """
    Request a shutdown of the running project.
    """

    pass
