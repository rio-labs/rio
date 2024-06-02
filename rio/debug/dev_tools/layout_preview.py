from __future__ import annotations

import io
from dataclasses import KW_ONLY
from typing import *  # type: ignore

import rio


class AlignmentControls(rio.Component):
    label: str
    enabled: bool
    value: float

    def build(self) -> rio.Component:
        # Allow enabling / disabling alignment
        result = rio.Row(
            rio.Text(
                self.label,
                align_x=0,
                width="grow",
            ),
            rio.Switch(is_on=self.bind().enabled),
            spacing=1,
        )

        # If enabled, add a slider to control the alignment value
        if self.enabled:
            result = rio.Column(
                result,
                rio.Slider(
                    value=self.bind().value,
                    minimum=0,
                    maximum=1,
                ),
                spacing=0.5,
            )

        return result


class LayoutPreview(rio.Component):
    component: rio.Component

    _: KW_ONLY

    _width: float = 0
    _height: float = 0

    _margin_left: float = 0
    _margin_top: float = 0
    _margin_right: float = 0
    _margin_bottom: float = 0

    _enable_align_x: bool = False
    _enable_align_y: bool = False

    _align_x: float = 0.5
    _align_y: float = 0.5

    def _build_result(self) -> rio.Component:
        child_rectangle = rio.Card(
            content=rio.Text(type(self.component).__name__),
            color="hud",
            width=self._width,
            height=self._height,
            margin_left=self._margin_left,
            margin_top=self._margin_top,
            margin_right=self._margin_right,
            margin_bottom=self._margin_bottom,
        )

        margin_rectangle = rio.Rectangle(
            content=child_rectangle,
            fill=self.session.theme.neutral_palette.foreground.replace(
                opacity=0.2
            ),
            corner_radius=1,
            align_x=self._align_x if self._enable_align_x else None,
            align_y=self._align_y if self._enable_align_y else None,
        )

        return rio.Rectangle(
            content=margin_rectangle,
            fill=self.session.theme.neutral_palette.background_variant,
            height=20,
            corner_radius=1,
            width="grow",
        )

    def _build_source_code(self) -> rio.Component:
        source = io.StringIO()
        source.write(
            """SampleComponent(
    ...
"""
        )

        # Size
        if self._width != 0:
            source.write(f"    width={self._width:.1f},\n")

        if self._height != 0:
            source.write(f"    height={self._height:.1f},\n")

        # Margins
        single_x_margin = self._margin_left == self._margin_right
        single_y_margin = self._margin_top == self._margin_bottom

        margins: list[tuple[str, float]] = []

        if single_x_margin and single_y_margin:
            margins.append(("margin", self._margin_left))

        else:
            if single_x_margin:
                margins.append(("margin_x", self._margin_left))
            else:
                margins.append(("margin_left", self._margin_left))
                margins.append(("margin_right", self._margin_right))

            if single_y_margin:
                margins.append(("margin_y", self._margin_top))
            else:
                margins.append(("margin_top", self._margin_top))
                margins.append(("margin_bottom", self._margin_bottom))

        for margin_name, margin_value in margins:
            margin_value = round(margin_value, 1)

            if margin_value != 0:
                source.write(f"    {margin_name}={margin_value},\n")

        # Alignment
        if self._enable_align_x:
            source.write(f"    align_x={self._align_x:.2f},\n")

        if self._enable_align_y:
            source.write(f"    align_y={self._align_y:.2f},\n")

        source.write(")")

        # Display the source code
        return rio.CodeBlock(
            source.getvalue(),
            language="python",
        )

    def _build_explanations(self) -> rio.Component:
        # Some messages depend on data about the component
        COMPONENT_WIDTH = 7.6
        COMPONENT_HEIGHT = 1

        # Find all messages to display
        explanations: List[str] = []

        if not self._enable_align_x and not self._enable_align_y:
            explanations.append(
                "The component is using the full size of its parent because it doesn't have any alignment set."
            )

        else:
            if self._enable_align_x:
                if self._width < COMPONENT_WIDTH:
                    explanations.append(
                        "The configured width is less than the component's natural width. Because of this, the natural width of the component is used."
                    )
                else:
                    explanations.append(
                        "The component's width was overridden by your settings."
                    )
            else:
                explanations.append(
                    "The component is using the full width of its parent because it doesn't have any horizontal alignment set."
                )

            if self._enable_align_y:
                if self._height < COMPONENT_HEIGHT:
                    explanations.append(
                        "The configured height is less than the component's natural height. Because of this, the natural height of the component is used."
                    )
                else:
                    explanations.append(
                        "The component's height was overridden by your settings."
                    )
            else:
                explanations.append(
                    "The component is using the full height of its parent because it doesn't have any vertical alignment set."
                )

        # Combine everything
        if explanations:
            return rio.Column(
                # rio.Text("Explanations", style="heading3"),
                *[
                    rio.Text(
                        explanation,
                        justify="left",
                        wrap=True,
                        style=rio.TextStyle(
                            italic=True,
                        ),
                    )
                    for explanation in explanations
                ],
                spacing=0.5,
                margin_y=0.5,
            )

        return rio.Spacer(height=0)

    def _build_controls(self) -> rio.Component:
        controls_margin = rio.Column(
            rio.Text("Margin", style="heading3"),
            rio.Grid(
                [
                    rio.Text("Left"),
                    rio.Slider(
                        value=self.bind()._margin_left,
                        minimum=0,
                        maximum=5,
                        width="grow",
                    ),
                    rio.Text(f"{self._margin_left:.1f}"),
                ],
                [
                    rio.Text("Top"),
                    rio.Slider(
                        value=self.bind()._margin_top,
                        minimum=0,
                        maximum=5,
                        width="grow",
                    ),
                    rio.Text(f"{self._margin_top:.1f}"),
                ],
                [
                    rio.Text("Right"),
                    rio.Slider(
                        value=self.bind()._margin_right,
                        minimum=0,
                        maximum=5,
                        width="grow",
                    ),
                    rio.Text(f"{self._margin_right:.1f}"),
                ],
                [
                    rio.Text("Bottom"),
                    rio.Slider(
                        value=self.bind()._margin_bottom,
                        minimum=0,
                        maximum=5,
                        width="grow",
                    ),
                    rio.Text(f"{self._margin_bottom:.1f}"),
                ],
                row_spacing=1,
                column_spacing=1,
                margin=0.8,
            ),
            spacing=1,
            align_y=0,
        )

        controls_size = rio.Column(
            rio.Text("Size", style="heading3"),
            rio.Grid(
                [
                    rio.Text("Width"),
                    rio.Slider(
                        value=self.bind()._width,
                        minimum=0,
                        maximum=30,
                        width="grow",
                    ),
                    rio.Text(
                        f"{self._width:.1f}",
                        width=3.0,
                    ),
                ],
                [
                    rio.Text("Height"),
                    rio.Slider(
                        value=self.bind()._height,
                        minimum=0,
                        maximum=10,
                        width="grow",
                    ),
                    rio.Text(
                        f"{self._height:.1f}",
                        width=3.0,
                    ),
                ],
                row_spacing=0.5,
                column_spacing=0.5,
                margin=0.8,
            ),
            spacing=0.5,
            align_y=0,
        )

        controls_alignment = rio.Column(
            rio.Text("Alignment", style="heading3"),
            rio.Column(
                AlignmentControls(
                    label="Align X",
                    enabled=self.bind()._enable_align_x,
                    value=self.bind()._align_x,
                ),
                AlignmentControls(
                    label="Align Y",
                    enabled=self.bind()._enable_align_y,
                    value=self.bind()._align_y,
                ),
                spacing=0.5,
                margin=0.8,
            ),
            spacing=0.5,
            align_y=0,
        )

        return rio.Row(
            controls_margin,
            controls_size,
            controls_alignment,
            proportions="homogeneous",
            spacing=0.5,
        )

    def build(self) -> rio.Component:
        return rio.Column(
            self._build_result(),
            self._build_explanations(),
            self._build_controls(),
            self._build_source_code(),
            spacing=0.5,
            margin=1,
        )
