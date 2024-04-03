from typing import *  # type: ignore

import rio


class Project(rio.Component):
    name: str
    details: str
    link: rio.URL

    def on_press(self) -> None:
        self.session.navigate_to(self.link)

    def build(self) -> rio.Component:
        return rio.Card(
            rio.Column(
                rio.Text(
                    self.name,
                    style="heading3",
                ),
                rio.Text(
                    self.details,
                    multiline=True,
                ),
                spacing=0.5,
            ),
            on_press=self.on_press,
        )


class Projects(rio.Component):
    def build(self) -> rio.Component:
        return rio.Grid(
            (
                Project(
                    "uniserde",
                    "Pure Python, easy to use Serializer",
                    rio.URL("https://gitlab.com/Vivern/uniserde"),
                ),
                Project(
                    "uniserde",
                    "Pure Python, easy to use Serializer",
                    rio.URL("https://gitlab.com/Vivern/uniserde"),
                ),
                Project(
                    "uniserde",
                    "Pure Python, easy to use Serializer",
                    rio.URL("https://gitlab.com/Vivern/uniserde"),
                ),
            ),
            (
                Project(
                    "uniserde",
                    "Pure Python, easy to use Serializer",
                    rio.URL("https://gitlab.com/Vivern/uniserde"),
                ),
                Project(
                    "uniserde",
                    "Pure Python, easy to use Serializer",
                    rio.URL("https://gitlab.com/Vivern/uniserde"),
                ),
                Project(
                    "uniserde",
                    "Pure Python, easy to use Serializer",
                    rio.URL("https://gitlab.com/Vivern/uniserde"),
                ),
            ),
            row_spacing=2,
            column_spacing=2,
        )
