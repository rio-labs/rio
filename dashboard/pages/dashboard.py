from __future__ import annotations

from typing import *  # type: ignore

import psutil

import rio

from .. import components as comps


class Dashboard(rio.Component):
    banner_message: str | None = None

    def build(self) -> rio.Component:
        # Grids need more information about their children than most components.
        # It's often easier to create them first, then add children afterwards.
        grid = rio.Grid(
            width="grow",
            height="grow",
            row_spacing=2,
            column_spacing=2,
            margin=2,
        )

        # The banner will display a message at the top of the page.
        grid.add(
            rio.Banner(
                self.banner_message,
                style="info",
            ),
            row=0,
            column=0,
            width=4,
        )

        # CPU
        grid.add(
            comps.StatCard(
                icon="memory",
                # color=rio.Color.RED,
                color=self.session.theme.primary_color,
                title="Processor",
                current=f"{psutil.cpu_percent()}%",
            ),
            row=1,
            column=0,
        )

        # Memory
        mem = psutil.virtual_memory()
        grid.add(
            comps.StatCard(
                icon="apps",
                # color=rio.Color.GREEN,
                color=self.session.theme.primary_color,
                title="Memory",
                current=f"{mem.used / 2**30:.0f}GiB",
                maximum=f"{mem.total / 2 ** 30:.0f}GiB",
            ),
            row=1,
            column=1,
        )

        # Network
        net = psutil.net_io_counters()
        grid.add(
            comps.StatCard(
                icon="wifi",
                # color=rio.Color.BLUE,
                color=self.session.theme.primary_color,
                title="Network",
                current=f"{net.bytes_sent / 2**30:.0f}GiB",
            ),
            row=1,
            column=2,
        )

        # Storage
        disk = psutil.disk_usage("/")
        grid.add(
            comps.StatCard(
                icon="storage",
                # color=rio.Color.ORANGE,
                color=self.session.theme.primary_color,
                title="Storage",
                current=f"{disk.used / 2**30:.0f}GiB",
                maximum=f"{disk.total / 2**30:.0f}GiB",
            ),
            row=1,
            column=3,
        )

        grid.add(
            comps.History(
                height="grow",
            ),
            row=2,
            column=0,
            width=3,
        )
        grid.add(
            comps.ProcessList(
                align_y=0,
            ),
            row=2,
            column=3,
        )

        return rio.Row(
            comps.Sidebar(),
            grid,
        )
