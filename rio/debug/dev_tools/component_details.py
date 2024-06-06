from __future__ import annotations

from dataclasses import KW_ONLY
from pathlib import Path
from typing import *  # type: ignore

import rio
import rio.docs

try:
    RIO_PATH = Path(rio.__file__).parent
except Exception:
    # Use a dummy path. It doesn't really matter, as long as it doesn't crash
    # `Path.is_relative_to`
    RIO_PATH = Path.cwd() / "rio"


class ComponentDetails(rio.Component):
    component_id: int

    _: KW_ONLY

    on_switch_to_layout_view: rio.EventHandler[[]] = None

    component_natural_width: float = 0
    component_natural_height: float = 0

    component_allocated_width: float = 0
    component_allocated_height: float = 0

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
            (allocation,) = await self.session._get_component_layouts(
                [component_id]
            )
        except KeyError:
            return

        # If the current component has changed while the values were fetched,
        # don't update the state
        if self.component_id != component_id:
            return

        # Publish the results
        self.component_natural_width = allocation.natural_width
        self.component_natural_height = allocation.natural_height
        self.component_allocated_width = allocation.allocated_width
        self.component_allocated_height = allocation.allocated_height

    def build(self) -> rio.Component:
        # Get the target component
        try:
            target = self.session._weak_components_by_id[self.component_id]

        # If the component can't be found, don't display anything. This can
        # happen, e.g. with injected components or due to network lag.
        except KeyError:
            return rio.Spacer(height=0)

        # Get the debug details. This is a dictionary which contains all
        # keys/values the component has, excluding internals.
        debug_details = target._get_debug_details()

        # Build the result. There is no need to add a heading, because it was
        # already handled by the parent component.
        result = DetailsGrid()

        # Which file/line was this component instantiated from?
        file, line = target._creator_stackframe_

        # If it was instantiated somewhere in the rio internals, don't show it
        if not file.is_relative_to(RIO_PATH):
            try:
                file = file.relative_to(Path.cwd())
            except ValueError:
                pass

            result.add_full_width(
                rio.Markdown(
                    f"Created in `{file}`, line {line}",
                    margin_top=0.5,
                    margin_bottom=1,
                ),
            )

        # The component's attributes
        self._build_details(result, target, debug_details)

        # Link to docs
        if type(target)._rio_builtin_:
            docs_url = rio.docs.build_documentation_url(type(target).__name__)
            link_color = self.session.theme.secondary_color

            result.add_full_width(
                rio.Link(
                    rio.Row(
                        rio.Icon("material/library-books", fill=link_color),
                        rio.Text(
                            "Read the Docs",
                            style=rio.TextStyle(fill=link_color),
                        ),
                        spacing=0.5,
                        margin_top=1,
                        align_x=0,
                    ),
                    docs_url,
                    # TODO: Support icons in links
                    open_in_new_tab=True,
                    margin_left=0.5,
                )
            )

        # Push all of the content to the left. This could be done by aligning
        # the entire Grid, but that would ellipsize some long texts. Instead,
        # add a Spacer into a fifth column, which will take up any unused space.
        result.add(
            rio.Spacer(height=0),
            column=4,
        )

        # Done!
        return result.as_rio_component()

    def _build_details(
        self,
        result: DetailsGrid,
        target: rio.Component,
        debug_details: dict[str, Any],
    ) -> None:
        # Add the component's attributes
        result.add_heading3("Custom Attributes", margin_top=0)
        has_custom_attributes: bool = False

        for prop_name, prop_value in debug_details.items():
            # Make sure to skip any which already have custom tailored cells
            if prop_name in (
                "width",
                "height",
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
            result.add_row(prop_name, repr(prop_value))
            has_custom_attributes = True

        if not has_custom_attributes:
            result.add_full_width(
                rio.Text(
                    "This component has no custom attributes",
                    justify="left",
                    style="dim",
                    margin=0.6,
                )
            )

        # Margins
        result.add_heading3("Layout")
        margin_left = target._effective_margin_left
        margin_top = target._effective_margin_top
        margin_right = target._effective_margin_right
        margin_bottom = target._effective_margin_bottom

        single_x_margin = margin_left == margin_right
        single_y_margin = margin_top == margin_bottom

        if single_x_margin and single_y_margin:
            result.add_label("margin", column=0)
            result.add_value(str(margin_left), column=1)

            result.row += 1

        else:
            if single_x_margin:
                result.add_label("margin_x", column=0)
                result.add_value(str(margin_left), column=1)

            else:
                result.add_label("margin_left", column=0)
                result.add_value(str(margin_left), column=1)

                result.add_label("margin_right", column=2)
                result.add_value(str(margin_right), column=3)

            result.row += 1

            if single_y_margin:
                result.add_label("margin_y", column=0)
                result.add_value(str(margin_top), column=1)

            else:
                result.add_label("margin_top", column=0)
                result.add_value(str(margin_top), column=1)

                result.add_label("margin_bottom", column=2)
                result.add_value(str(margin_bottom), column=3)

            result.row += 1

        result.add_spacing()

        # Size
        if "width" in debug_details or "height" in debug_details:
            try:
                py_width_str = debug_details["width"]
            except KeyError:
                py_width_str = "-"
            else:
                if isinstance(py_width_str, (int, float)):
                    py_width_str = round(py_width_str, 2)

                py_width_str = repr(py_width_str)

            try:
                py_height_str = debug_details["height"]
            except KeyError:
                py_height_str = "-"
            else:
                if isinstance(py_height_str, (int, float)):
                    py_height_str = round(py_height_str, 2)

                py_height_str = repr(py_height_str)

            # Add some extra spacing
            result.row += 1

            # Header
            result.add_label("width", column=1, justify="right")
            result.add_label("height", column=2, justify="right")
            result.row += 1

            # The size as specified in Python
            result.add_label("python", column=0)
            result.add_value(py_width_str, column=1, justify="right")
            result.add_value(py_height_str, column=2, justify="right")
            result.row += 1

            # The component's natural size
            result.add_label("natural", column=0)
            result.add_value(
                str(round(self.component_natural_width, 2)),
                column=1,
                justify="right",
            )
            result.add_value(
                str(round(self.component_natural_height, 2)),
                column=2,
                justify="right",
            )
            result.row += 1

            # The component's allocated size
            result.add_label("allocated", column=0)
            result.add_value(
                str(round(self.component_allocated_width, 2)),
                column=1,
                justify="right",
            )
            result.add_value(
                str(round(self.component_allocated_height, 2)),
                column=2,
                justify="right",
            )
            result.row += 1

        result.add_spacing()

        # Alignment
        if "align_x" in debug_details or "align_y" in debug_details:
            result.add_label("align_x", column=0)
            result.add_value(str(debug_details.get("align_x", "-")), column=1)

            result.add_label("align_y", column=2)
            result.add_value(str(debug_details.get("align_y", "-")), column=3)

            result.row += 1

        # Offer to show the detailed layout subpage
        result.add_full_width(
            rio.Button(
                "Layout View",
                icon="space-dashboard",
                on_press=self.on_switch_to_layout_view,
                style="minor",
                margin_top=0.5,
            )
        )


class DetailsGrid:
    def __init__(self) -> None:
        self.grid = rio.Grid(row_spacing=0.5, column_spacing=0.5)
        self.row = 0

    def add_row(self, label: str, value: str) -> None:
        self.add_label(
            label,
            column=0,
            component_width=8,
            ellipsize=True,
        )
        self.add_value(
            value,
            column=1,
            width=3,
            ellipsize=True,
        )
        self.row += 1

    def add_label(
        self,
        text: str,
        *,
        row: int | None = None,
        column: int,
        justify: Literal["left", "center", "right"] = "right",
        ellipsize: bool = False,
        component_width: float = 0,
        column_width: int = 1,
    ) -> None:
        self.add(
            rio.Text(
                text,
                style="dim",
                wrap="ellipsize" if ellipsize else False,
                justify=justify,
                width=component_width,
            ),
            row=row,
            column=column,
            width=column_width,
        )

    def add_value(
        self,
        value: str,
        *,
        row: int | None = None,
        column: int,
        width: int = 1,
        justify: Literal["left", "center", "right"] = "left",
        ellipsize: bool = False,
    ) -> None:
        self.add(
            rio.Text(
                value,
                justify=justify,
                width="grow" if ellipsize else "natural",
                wrap="ellipsize" if ellipsize else False,
            ),
            row=row,
            column=column,
            width=width,
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

    def add_full_width(self, child: rio.Component) -> None:
        self.grid.add(
            child,
            self.row,
            0,
            width=5,
        )
        self.row += 1

    def add_heading3(
        self,
        heading: str,
        *,
        margin_top=1,
    ) -> None:
        self.add_full_width(
            rio.Text(
                text=heading,
                style="heading3",
                justify="left",
                margin_top=margin_top,
            )
        )

    def add_spacing(self, amount: float = 1) -> None:
        self.add_full_width(rio.Spacer(height=amount))

    def as_rio_component(self) -> rio.Component:
        return self.grid
