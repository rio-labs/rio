import time
import typing as t
from pathlib import Path

import watchfiles

from ... import project_config
from . import run_models


class FileWatcherWorker:
    def __init__(
        self,
        *,
        push_event: t.Callable[[run_models.Event], None],
        proj: project_config.RioProjectConfig,
    ) -> None:
        self.push_event = push_event
        self.proj = proj

    async def run(self) -> None:
        """
        Watch the project directory for changes and report them as events.
        """
        # Watch the project directory
        async for changes in watchfiles.awatch(self.proj.project_directory):
            timestamp = time.monotonic_ns()

            for change, path in changes:
                path = Path(path)

                # Not all files trigger a reload
                if not self.proj.file_is_path_of_project(path):
                    continue

                # Report the change
                self.push_event(run_models.FileChanged(timestamp, path))
