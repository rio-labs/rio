from __future__ import annotations

from dataclasses import KW_ONLY
from typing import *  # type: ignore

import rio
import rio.components.fundamental_component
import rio.components.layout_display

from . import layout_explanation


class MultiSwitch(rio.Component):
    options: list[str]
    selected_value: str

    _: KW_ONLY

    on_change: rio.EventHandler[str]

    async def _select_value(self, value: str) -> None:
        self.selected_value = value
        await self.call_event_handler(self.on_change, value)

    def build(self) -> rio.Component:
        result = rio.Row()

        for ii, value in enumerate(self.options):
            corner_radii = [0, 0, 0, 0]

            if ii == 0:
                corner_radii[0] = corner_radii[3] = 9999

            if ii == len(self.options) - 1:
                corner_radii[1] = corner_radii[2] = 9999

            is_active = value == self.selected_value

            if is_active:
                palette = self.session.theme.secondary_palette
                color = palette.background
            else:
                palette = self.session.theme.neutral_palette
                color = palette.background_variant

            result.add(
                rio.MouseEventListener(
                    rio.Rectangle(
                        content=rio.Text(
                            value,
                            style=rio.TextStyle(fill=palette.foreground),
                            margin=0.3,
                        ),
                        fill=color,
                        corner_radius=tuple(corner_radii),  # type: ignore
                        hover_fill=None
                        if is_active
                        else palette.background_active,
                        transition_time=0,
                        ripple=not is_active,
                        cursor=rio.CursorStyle.POINTER,
                    ),
                    on_press=lambda _, value=value: self._select_value(value),
                )
            )

        return result


class HelpAnchor(rio.Component):
    content: str

    def build(self) -> rio.Component:
        return rio.Tooltip(
            # The rectangle increases the area the user can hover over
            anchor=rio.Rectangle(
                content=rio.Row(
                    rio.Icon("help", fill="secondary"),
                    rio.Text(
                        "Help",
                        style=rio.TextStyle(
                            fill=self.session.theme.secondary_color
                        ),
                    ),
                    spacing=0.5,
                    margin_y=0.5,
                    align_x=0,
                ),
                fill=rio.Color.TRANSPARENT,
            ),
            tip=rio.Markdown(
                self.content,
                width=25,
            ),
            position="left",
            gap=2,
        )


class SizeControls(rio.Component):
    label: Literal["width", "height"]
    value: Literal["natural", "grow"] | float

    _: KW_ONLY

    on_change: rio.EventHandler[Literal["natural", "grow"] | float] = None

    def __post_init__(self) -> None:
        assert isinstance(self.value, (int, float)) or self.value in (
            "natural",
            "grow",
        ), self.value

    async def _on_multi_switch_change(self, value: str) -> None:
        if value.startswith("natural "):
            self.value = "natural"
        elif value == "grow":
            self.value = "grow"
        else:
            self.value = 0

        await self.call_event_handler(self.on_change, self.value)

    async def _on_number_input_change(
        self,
        event: rio.NumberInputChangeEvent,
    ) -> None:
        self.value = event.value

        await self.call_event_handler(self.on_change, self.value)

    def build(self) -> rio.Component:
        natural_name = f"natural {self.label}"
        grow_name = "grow"
        custom_name = f"custom {self.label}"

        # Custom?
        if isinstance(self.value, (int, float)):
            number_input = rio.NumberInput(
                value=self.value,
                on_change=self._on_number_input_change,
            )
            selected_value = custom_name
        elif self.value == "natural":
            number_input = None
            selected_value = natural_name
        else:
            assert self.value == "grow", self.value
            number_input = None
            selected_value = grow_name

        # Build up the UI
        return rio.Column(
            MultiSwitch(
                [natural_name, grow_name, custom_name],
                selected_value=selected_value,
                on_change=self._on_multi_switch_change,
            ),
            rio.Switcher(number_input),
            spacing=0.5,
        )


class AlignmentControls(rio.Component):
    label: str
    value: float | None

    _: KW_ONLY

    on_change: rio.EventHandler[float | None] = None

    async def _on_switch_change(self, event: rio.SwitchChangeEvent) -> None:
        if event.is_on:
            self.value = 0.5
        else:
            self.value = None

        await self.call_event_handler(self.on_change, self.value)

    async def _on_slider_change(self, event: rio.SliderChangeEvent) -> None:
        self.value = event.value
        await self.call_event_handler(self.on_change, self.value)

    def build(self) -> rio.Component:
        # If enabled, add a slider to control the alignment value
        if self.value is None:
            slider = None
        else:
            slider = rio.Slider(
                value=self.value,
                minimum=0,
                maximum=1,
                on_change=self._on_slider_change,
                margin_top=1,
                margin_bottom=0.5,
            )

        # Allow enabling / disabling alignment
        return rio.Column(
            rio.Row(
                rio.Text(
                    self.label,
                    align_x=0,
                    width="grow",
                ),
                rio.Switch(
                    is_on=self.value is not None,
                    on_change=self._on_switch_change,
                ),
                align_x=0,
                spacing=0.5,
            ),
            rio.Switcher(slider),
        )


class LayoutSubpage(rio.Component):
    component_id: int

    _: KW_ONLY

    _layout_explanation_x: str = ""
    _layout_explanation_y: str = ""

    def get_target_component(self) -> rio.Component:
        return self.session._weak_components_by_id[self.component_id]

    @rio.event.on_populate
    async def _on_populate(self) -> None:
        # Get human-readable layout explanations
        target = self.get_target_component()

        (
            self._layout_explanation_x,
            self._layout_explanation_y,
        ) = await layout_explanation.explain_layout(self.session, target)

    #     async def _set_client_side_property(self, name: str, value: Any) -> None:
    #         name_js = json.dumps(name)
    #         value_js = json.dumps(value)

    #         await self.session._evaluate_javascript(
    #             f"""
    # // Log the change
    # const attrName = {name_js};
    # const attrValue = {value_js};

    # console.debug(`Dev-Tools: Setting \\`${{attrName}}\\` of component #{self.component_id} to \\`${{attrValue}}\\``);

    # // Update the state. This will trigger a re-layout if needed
    # let component = componentsById[{self.component_id}];
    # component._setStateDontNotifyBackend(
    #     {{
    #         attrName: attrValue,
    #     }},
    #     new Set(),
    # );
    # """
    #         )

    def _update_target_attribute(self, name: str, value: Any) -> None:
        """
        Updates an attribute of the target component.

        This is more complicated than just setting the attribute, because Rio
        must be notified of the change in order to update the display.
        """
        target = self.get_target_component()

        # Assign the new value to the Python instance
        setattr(target, name, value)

        # # Fundamental components have no ability to rebuild and must thus be
        # # updated in-place, client-side
        # if (
        #     isinstance(
        #         target,
        #         rio.components.fundamental_component.FundamentalComponent,
        #     )
        #     or False
        # ):
        #     self.session.create_task(
        #         self._set_client_side_property(name, value),
        #         name="Client-side property update task by `_update_attribute`",
        #     )

        # # High-level components will automatically mark themselves as dirty, but
        # # won't trigger a resync. Do that now.
        # else:
        self.session.create_task(
            self.session._refresh(),
            name="Refresh task by `_update_attribute`",
        )

    def _build_explanations(self) -> rio.Component:
        return rio.Markdown(
            f"**Width:** {self._layout_explanation_x}\n\n**Height:** {self._layout_explanation_y}",
        )

    def _build_margin_controls(self) -> rio.Component:
        result = rio.Grid(
            row_spacing=0.3,
            column_spacing=0.3,
        )

        # Add a visual stand-in for the target component
        target = self.get_target_component()
        result.add(
            rio.Card(
                content=rio.Text(type(target).__name__),
                color="secondary",
                corner_radius=self.session.theme.corner_radius_small,
            ),
            1,
            1,
        )

        # And controls for the margin
        result.add(
            rio.NumberInput(
                label="Left",
                minimum=0,
                on_change=lambda event: self._update_target_attribute(
                    "margin_left", event.value
                ),
            ),
            1,
            0,
        )

        result.add(
            rio.NumberInput(
                label="Top",
                minimum=0,
                on_change=lambda event: self._update_target_attribute(
                    "margin_top", event.value
                ),
            ),
            0,
            1,
        )

        result.add(
            rio.NumberInput(
                label="Right",
                minimum=0,
                on_change=lambda event: self._update_target_attribute(
                    "margin_right", event.value
                ),
            ),
            1,
            2,
        )

        result.add(
            rio.NumberInput(
                label="Bottom",
                minimum=0,
                on_change=lambda event: self._update_target_attribute(
                    "margin_bottom", event.value
                ),
            ),
            2,
            1,
        )

        result.add(
            HelpAnchor(
                """
Margin adds empty space around the component. You can either specify each side
separately, or use one of the shortcuts `margin`, `margin_x`, `margin_y`.
                """,
            ),
            3,
            0,
            width=3,
        )

        return result

    def _build_size_controls(self) -> rio.Component:
        target_component = self.get_target_component()

        return rio.Column(
            SizeControls(
                label="width",
                value=target_component.width,
                on_change=lambda value: self._update_target_attribute(
                    "width", value
                ),
            ),
            SizeControls(
                label="height",
                value=target_component.height,
                on_change=lambda value: self._update_target_attribute(
                    "height", value
                ),
            ),
            HelpAnchor(
                """
`"natural"` components take up as little space as necessary.

Components with `"grow"` take priority when too much space is available. This is
only relevant in components that have multiple children, such as `Row` and
`Column`.

Components with custom size take up at least the specified amount of space, but
never less than their natural size.

Above all, **components always take up all superfluous space from their
parent**. If you don't want for that to happen, set an alignment.
                """,
            ),
            spacing=0.5,
        )

    def _build_alignment_controls(self) -> rio.Component:
        target = self.get_target_component()

        return rio.Column(
            AlignmentControls(
                label="Align X",
                value=target.align_x,
                on_change=lambda value: self._update_target_attribute(
                    "align_x", value
                ),
            ),
            AlignmentControls(
                label="Align Y",
                value=target.align_y,
                on_change=lambda value: self._update_target_attribute(
                    "align_y", value
                ),
            ),
            HelpAnchor(
                """
Unaligned components take up the full space assigned by their parent. Aligned
components only take up as little space as necessary to display their content.

Components with an alignment of `0` are left/top-aligned, `0.5` are centered,
and `1` are right/bottom-aligned.
                    """
            ),
            spacing=0.5,
        )

    def build(self) -> rio.Component:
        return rio.Column(
            rio.components.layout_display.LayoutDisplay(
                component_id=self.bind().component_id,
                max_requested_height=20,
            ),
            rio.Revealer(
                header="Explanation",
                content=self._build_explanations(),
                header_style="heading3",
                is_open=True,
            ),
            rio.Revealer(
                header="Margin",
                content=self._build_margin_controls(),
                header_style="heading3",
            ),
            rio.Revealer(
                header="Size",
                content=self._build_size_controls(),
                header_style="heading3",
            ),
            rio.Revealer(
                header="Alignment",
                content=self._build_alignment_controls(),
                header_style="heading3",
            ),
            rio.Link(
                rio.Row(
                    rio.Icon("material/library-books", fill="secondary"),
                    rio.Text(
                        "Layouting Quickstart",
                        style=rio.TextStyle(
                            fill=self.session.theme.secondary_color
                        ),
                    ),
                    spacing=0.5,
                    margin_y=1,
                    align_x=0,
                ),
                target_url="https://rio.dev/docs/howto/layout-guide",
                open_in_new_tab=True,
                align_x=0,
            ),
            spacing=0.5,
        )
