import rio

from ...components import component_tree
from . import component_details


class DocsPage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text(
                "Documentation",
                style="heading2",
                margin=1,
                align_x=0,
            ),
            rio.Column(
                rio.Text(
                    "New here? The Rio tutorial can help you get started.",
                    multiline=True,
                ),
                rio.Button(
                    "Read the Tutorial",
                    icon="school",
                    style="minor",
                    margin=1,
                ),
                spacing=1,
                height="grow",
                align_y=0.5,
                margin=1,
            ),
        )
