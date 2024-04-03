from __future__ import annotations

from typing import *  # type: ignore

import psutil

import rio

from .. import components as comps


class ProcessList(rio.Component):
    example_state: str = "For demonstration purposes"

    def build(self) -> rio.Component:
        entries = []

        # entries.append(
        #     rio.SimpleListItem(
        #         text="Task 1",
        #         secondary_text="This is a description of task 1",
        #         key="task1",
        #     ),
        # )

        # entries.append(
        #     rio.SimpleListItem(
        #         text="Task 2",
        #         secondary_text="This is a description of task 2",
        #         key="task2",
        #     ),
        # )
        processes = list(psutil.process_iter())
        processes.sort(key=lambda proc: proc.name())
        processes = processes[:10]

        for proc in processes:
            entries.append(
                rio.SimpleListItem(
                    text=proc.name(),
                    secondary_text=f"PID: {proc.pid}",
                    key=str(proc.pid),
                ),
            )

        return rio.Card(
            rio.Column(
                rio.Text(
                    "Tasks",
                    style="heading2",
                    margin=1,
                ),
                rio.ListView(
                    *entries,
                ),
            ),
            # color="primary",
        )
