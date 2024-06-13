import time
from pathlib import Path
from typing import *  # type: ignore

import watchfiles

from .. import project
from . import run_models


class FileWatcherWorker:
    def __init__(
        self,
        *,
        push_event: Callable[[run_models.Event], None],
        proj: project.RioProject,
    ) -> None:
        self.push_event = push_event
        self.proj = proj

    async def run(self) -> None:
        """
        Watch the project directory for changes and report them as events.
        """
        # Watch all files
        filter = watchfiles.DefaultFilter()

        # Watch the project directory
        async for changes in watchfiles.awatch(
            self.proj.project_directory, watch_filter=filter
        ):
            for change, path in changes:
                path = Path(path)

                # Not all files trigger a reload
                if not self.proj.file_is_path_of_project(path):
                    continue

                # Report the change
                self.push_event(
                    run_models.FileChanged(
                        time.monotonic_ns(),
                        path,
                    )
                )
