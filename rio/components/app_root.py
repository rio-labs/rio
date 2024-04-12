from __future__ import annotations

from dataclasses import KW_ONLY
from typing import *  # type: ignore

import rio

from . import class_container, component

__all__ = [
    "AppRoot",
]


class AppTopBar(component.Component):
    # TODO
    on_press_open: rio.EventHandler[[]] = None

    def build(self) -> rio.Component:
        thm = self.session.theme

        icons = []
        for icon in ("material/castle", "material/error", "material/archive"):
            icons.append(
                rio.IconButton(
                    icon,
                    style="plain",
                    size=3,
                )
            )

        return class_container.ClassContainer(
            content=rio.Row(
                rio.IconButton(
                    "material/menu",
                    style="plain",
                    margin_right=1,
                    size=3,
                    on_press=self.on_press_open,
                ),
                rio.Text(
                    self.session.app.name,
                    style=rio.TextStyle(
                        font_size=1.8,
                        fill=thm.primary_palette.foreground,
                    ),
                ),
                rio.Spacer(),
                rio.Row(*icons, spacing=2),
            ),
            classes=["rio-switcheroo-primary"],
            margin_x=1,
            margin_y=0.1,
        )


class Sidebar(component.Component):
    on_press_close: rio.EventHandler[[]] = None

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Row(
                rio.IconButton(
                    "material/menu-open",
                    style="plain",
                    size=3,
                    on_press=self.on_press_close,
                ),
                rio.Column(
                    rio.Text(
                        self.session.app.name,
                        style="heading2",
                        justify="left",
                    ),
                    rio.Text(
                        "TODO: Subtext",
                        style="dim",
                        justify="left",
                    ),
                    align_y=0,
                ),
                spacing=1,
                margin_x=1,
                margin_y=1,
                align_x=0,
            ),
            rio.SwitcherBar(
                names=["Foo", "Bar"],
                values=["foo", "bar"],
                orientation="vertical",
                width=25,
                margin=2,
                color="primary",
            ),
            rio.Spacer(),
            rio.SwitcherBar(
                names=["Settings"],
                values=["settings"],
                orientation="vertical",
                width=25,
                margin=2,
                color="primary",
            ),
        )


class AppRoot(component.Component):
    _: KW_ONLY
    fallback_build: Callable[[], rio.Component] | None = None

    _sidebar_is_open: bool = False

    def _on_press_open(self) -> None:
        self._sidebar_is_open = True

    def _on_press_close(self) -> None:
        self._sidebar_is_open = False

    def build(self) -> rio.Component:
        thm = self.session.theme

        return rio.Drawer(
            anchor=rio.Stack(
                rio.Rectangle(
                    fill=thm.primary_palette.background,
                ),
                rio.Column(
                    AppTopBar(
                        on_press_open=self._on_press_open,
                    ),
                    rio.Card(
                        rio.Stack(
                            rio.PageView(
                                fallback_build=self.fallback_build,
                            ),
                            rio.IconButton(
                                "material/castle",
                                align_x=1,
                                align_y=1,
                            ),
                        ),
                        corner_radius=(
                            thm.corner_radius_medium,
                            thm.corner_radius_medium,
                            0,
                            0,
                        ),
                        height="grow",
                    ),
                ),
            ),
            content=Sidebar(
                on_press_close=self._on_press_close,
            ),
            is_open=self._sidebar_is_open,
        )
