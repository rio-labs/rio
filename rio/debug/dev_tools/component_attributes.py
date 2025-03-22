from __future__ import annotations

import dataclasses
import typing as t
from pathlib import Path

import rio
import rio.docs

try:
    RIO_PATH = Path(rio.__file__).parent
except Exception:
    # Use a dummy path. It doesn't really matter, as long as it doesn't crash
    # `Path.is_relative_to`
    RIO_PATH = Path.cwd() / "rio"


class ComponentAttributes(rio.Component):
    component_id: int

    _: dataclasses.KW_ONLY

    on_switch_to_layout_view: rio.EventHandler[[]] = None

    component_natural_width: float = 0
    component_natural_height: float = 0

    component_allocated_inner_width: float = 0
    component_allocated_inner_height: float = 0

    @rio.event.on_populate
    async def fetch_client_side_details(self) -> None:
        """
        Fetch additional details about the component which are only known
        client-side. Stores them in the class.
        """
        # Remember which component the details are being fetched for
        component_id = self.component_id

        # Fetch the details
        try:
            (layout,) = await self.session._get_component_layouts(
                [component_id]
            )
        except KeyError:
            return

        # If the current component has changed while the values were fetched,
        # don't update the state
        if self.component_id != component_id:
            return

        # Publish the results
        self.component_natural_width = layout.natural_width
        self.component_natural_height = layout.natural_height
        self.component_allocated_inner_width = layout.allocated_inner_width
        self.component_allocated_inner_height = layout.allocated_inner_height

    def build(self) -> rio.Component:
        # Get the target component
        try:
            target = self.session._weak_components_by_id[self.component_id]

        # If the component can't be found, don't display anything. This can
        # happen, e.g. with injected components or due to network lag.
        except KeyError:
            return rio.Text(
                "The selected component no longer exists.",
                overflow="wrap",
            )

        # Build the result. There is no need to add a heading, because it was
        # already handled by the parent component.
        result_column = rio.Column()

        # Which file/line was this component instantiated from?
        file, line = target._creator_stackframe_

        # If it was instantiated somewhere in the rio internals, don't show it
        if not file.is_relative_to(RIO_PATH):
            try:
                file = file.relative_to(Path.cwd())
            except ValueError:
                pass

            result_column.add(
                rio.Markdown(
                    f"Created in `{file}`, line {line}",
                    margin_top=0.5,
                    margin_bottom=1,
                ),
            )

        # Get the debug details. This is a dictionary which contains all
        # keys/values the component has, excluding internals.
        debug_details = target._get_debug_details_()

        # The component's attributes
        self._build_details(result_column, target, debug_details)

        # Push the remaining content to the bottom
        result_column.add(rio.Spacer())

        # Link to docs
        if type(target)._rio_builtin_:
            docs_url = rio.URL(rio.docs.get_documentation_url(type(target)))

            result_column.add(
                rio.Link(
                    "Read the Docs",
                    icon="material/library_books",
                    target_url=docs_url,
                    open_in_new_tab=True,
                    margin_top=1,
                    align_x=0,
                )
            )

        # Offer to show the detailed layout subpage
        result_column.add(
            rio.Button(
                "Layout View",
                icon="material/space_dashboard",
                on_press=self.on_switch_to_layout_view,
                shape="rounded",
            )
        )

        # Done!
        return result_column

    def _build_details(
        self,
        result_column: rio.Column,
        target: rio.Component,
        debug_details: dict[str, t.Any],
    ) -> None:
        result_column.add(
            rio.Text(
                text="Custom Attributes",
                style="heading3",
                justify="left",
                margin_bottom=0.5,
            )
        )

        custom_attributes_grid = DetailsGrid()

        # Add the component's attributes
        has_custom_attributes: bool = False

        for prop_name, prop_value in debug_details.items():
            # Make sure to skip any which already have custom tailored cells
            if prop_name in (
                "min_width",
                "min_height",
                "grow_x",
                "grow_y",
                "margin",
                "margin_x",
                "margin_y",
                "margin_left",
                "margin_right",
                "margin_top",
                "margin_bottom",
                "align_x",
                "align_y",
            ):
                continue

            # Display this property
            custom_attributes_grid.add_row(
                prop_name, repr_attribute(prop_value)
            )
            has_custom_attributes = True

        if has_custom_attributes:
            result_column.add(custom_attributes_grid.as_rio_component())
        else:
            result_column.add(
                rio.Text(
                    "This component has no custom attributes",
                    justify="left",
                    style="dim",
                    margin=0.6,
                )
            )

        # Layout stuff: size, grow, alignment, margin
        result_column.add(
            rio.Text(
                "Layout",
                style="heading3",
                justify="left",
                margin_top=1,
            )
        )

        # Size
        size_grid = DetailsGrid(align_x=0.5)

        if "min_width" in debug_details or "min_height" in debug_details:
            try:
                py_min_width = debug_details["min_width"]
            except KeyError:
                py_min_width_str = "-"
            else:
                if isinstance(py_min_width, (int, float)):
                    py_min_width = round(py_min_width, 2)

                py_min_width_str = repr(py_min_width)

            try:
                py_min_height = debug_details["min_height"]
            except KeyError:
                py_min_height_str = "-"
            else:
                if isinstance(py_min_height, (int, float)):
                    py_min_height = round(py_min_height, 2)

                py_min_height_str = repr(py_min_height)

            # Add some extra spacing
            size_grid.row += 1

            # Header
            size_grid.add_label("width", column=1)
            size_grid.add_label("height", column=2)
            size_grid.row += 1

            # The minimum size as specified in Python
            size_grid.add_label("min", column=0)
            size_grid.add_value(py_min_width_str, column=1, justify="right")
            size_grid.add_value(py_min_height_str, column=2, justify="right")
            size_grid.row += 1

            # The component's natural size
            size_grid.add_label("natural", column=0)
            size_grid.add_value(
                str(round(self.component_natural_width, 2)),
                column=1,
                justify="right",
            )
            size_grid.add_value(
                str(round(self.component_natural_height, 2)),
                column=2,
                justify="right",
            )
            size_grid.row += 1

            # The component's allocated size
            size_grid.add_label("allocated", column=0)
            size_grid.add_value(
                str(round(self.component_allocated_inner_width, 2)),
                column=1,
                justify="right",
            )
            size_grid.add_value(
                str(round(self.component_allocated_inner_height, 2)),
                column=2,
                justify="right",
            )
            size_grid.row += 1

        result_column.add(
            size_grid.as_rio_component(),
        )

        result_column.add(rio.Spacer(min_height=1.5, grow_y=False))

        layout_grid = DetailsGrid(align_x=0.5)

        # Create some extra spacing in the middle
        layout_grid.add(rio.Spacer(min_width=1, grow_x=False), row=0, column=2)

        # Grow
        if "grow_x" in debug_details or "grow_y" in debug_details:
            layout_grid.add_label("grow_x", column=0)
            layout_grid.add_value(
                str(debug_details.get("grow_x", "-")), column=1
            )

            layout_grid.add_label("grow_y", column=3)
            layout_grid.add_value(
                str(debug_details.get("grow_y", "-")), column=4
            )

            layout_grid.row += 1

        # Alignment
        if "align_x" in debug_details or "align_y" in debug_details:
            layout_grid.add_label("align_x", column=0)
            layout_grid.add_value(
                str(debug_details.get("align_x", "-")), column=1
            )

            layout_grid.add_label("align_y", column=3)
            layout_grid.add_value(
                str(debug_details.get("align_y", "-")), column=4
            )

            layout_grid.row += 1

        # Margins
        margin_left = target._effective_margin_left_
        margin_top = target._effective_margin_top_
        margin_right = target._effective_margin_right_
        margin_bottom = target._effective_margin_bottom_

        single_x_margin = margin_left == margin_right
        single_y_margin = margin_top == margin_bottom

        if single_x_margin and single_y_margin:
            layout_grid.add_label("margin", column=0)
            layout_grid.add_value(str(margin_left), column=1)

            layout_grid.row += 1

        else:
            if single_x_margin:
                layout_grid.add_label("margin_x", column=0)
                layout_grid.add_value(str(margin_left), column=1)

            else:
                layout_grid.add_label("margin_left", column=0)
                layout_grid.add_value(str(margin_left), column=1)

                layout_grid.add_label("margin_right", column=3)
                layout_grid.add_value(str(margin_right), column=4)

            layout_grid.row += 1

            if single_y_margin:
                layout_grid.add_label("margin_y", column=0)
                layout_grid.add_value(str(margin_top), column=1)

            else:
                layout_grid.add_label("margin_top", column=0)
                layout_grid.add_value(str(margin_top), column=1)

                layout_grid.add_label("margin_bottom", column=3)
                layout_grid.add_value(str(margin_bottom), column=4)

            layout_grid.row += 1

        result_column.add(
            layout_grid.as_rio_component(),
        )


class DetailsGrid:
    def __init__(self, **kwargs) -> None:
        self.grid = rio.Grid(row_spacing=0.5, column_spacing=0.5, **kwargs)
        self.row = 0

    def add_row(self, label: str, value: str) -> None:
        self.add_label(label, column=0)
        self.add_value(value, column=1, ellipsize=True)
        self.row += 1

    def add_label(
        self,
        text: str,
        *,
        row: int | None = None,
        column: int,
        justify: t.Literal["left", "center", "right"] = "right",
    ) -> None:
        self.add(
            rio.Text(
                text,
                style="dim",
                justify=justify,
            ),
            row=row,
            column=column,
        )

    def add_value(
        self,
        value: str,
        *,
        row: int | None = None,
        column: int,
        justify: t.Literal["left", "center", "right"] = "left",
        ellipsize: bool = False,
    ) -> None:
        self.add(
            rio.Text(
                value,
                justify=justify,
                grow_x=ellipsize,
                overflow="ellipsize" if ellipsize else "nowrap",
            ),
            row=row,
            column=column,
        )

    def add(
        self,
        child: rio.Component,
        *,
        row: int | None = None,
        column: int,
        width: int = 1,
        height: int = 1,
    ) -> None:
        if row is None:
            row = self.row

        self.grid.add(child, row, column, width=width, height=height)

    def as_rio_component(self) -> rio.Component:
        return self.grid


def repr_attribute(value: object) -> str:
    # Some attributes can be extremely large. For example, a MediaPlayer might
    # be playing a 50MB bytes object. Limit the amount of data sent to the
    # frontend.
    if isinstance(value, (str, bytes, bytearray, memoryview)):
        max_length = 100
        return repr(value[:max_length])

    return repr(value)
