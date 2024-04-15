from typing import *  # type: ignore

import rio


class LayoutPreview(rio.Component):
    """
    WIP component for previewing the layout of another component in the
    debugger.
    """

    component: rio.Component

    def build(self) -> rio.Component:
        palette = self.session.theme.neutral_palette

        return rio.Rectangle(
            content=rio.Rectangle(
                margin=self.component.margin,
                margin_x=self.component.margin_x,
                margin_y=self.component.margin_y,
                margin_left=self.component.margin_left,
                margin_top=self.component.margin_top,
                margin_right=self.component.margin_right,
                margin_bottom=self.component.margin_bottom,
                width=self.component.width,
                height=self.component.height,
                align_x=self.component.align_x,
                align_y=self.component.align_y,
                fill=palette.background_active,
            ),
            fill=palette.background_variant,
        )
