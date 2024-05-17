from pathlib import Path
from typing import *  # type: ignore

import rio
import rio.docs

from ... import utils


class ComponentDetails(rio.Component):
    component_id: int

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
        response = await self.session._evaluate_javascript_and_get_result(
            f"""
            let component = componentsById[{component_id}];
            let rect = component.element.getBoundingClientRect();

            return [
                component.naturalWidth,
                component.naturalHeight,
                rect.width / pixelsPerRem,
                rect.height / pixelsPerRem,
            ];
            """
        )

        # If the current component has changed while the values were fetched,
        # don't update the state
        if self.component_id != component_id:
            return

        # Publish the results
        (
            self.component_natural_width,
            self.component_natural_height,
            self.component_allocated_width,
            self.component_allocated_height,
        ) = response

    def _get_effective_margins(self) -> Tuple[float, float, float, float]:
        return (
            utils.first_non_null(
                self.margin_left,
                self.margin_x,
                self.margin,
                0,
            ),
            utils.first_non_null(
                self.margin_top,
                self.margin_y,
                self.margin,
                0,
            ),
            utils.first_non_null(
                self.margin_right,
                self.margin_x,
                self.margin,
                0,
            ),
            utils.first_non_null(
                self.margin_bottom,
                self.margin_y,
                self.margin,
                0,
            ),
        )

    def build(self) -> rio.Component:
        # Get the target component
        try:
            target = self.session._weak_components_by_id[self.component_id]

        # In rare cases components can't be found, because they're created
        # client-side (e.g. injected margins). In this case, just don't display
        # anything.
        except KeyError:
            return rio.Spacer(height=0)

        # Create a grid with all the details
        result = rio.Grid(row_spacing=0.5, column_spacing=0.5)
        row_index = 0

        def add_cell(
            text: str,
            column_index: int,
            is_label: bool,
            *,
            width: int = 1,
        ) -> None:
            result.add(
                rio.Text(
                    text,
                    style="dim" if is_label else "text",
                    justify="right" if is_label else "left",
                ),
                row_index,
                column_index,
                width=width,
            )

        # Any values which should be displayed right in the title
        header_accessories = []

        if target.key is not None:
            header_accessories = [
                rio.Icon("material/key", fill="dim"),
                rio.Text(
                    target.key,
                    style="dim",
                    justify="left",
                ),
            ]

        # Title
        result.add(
            rio.Row(
                rio.Text(
                    type(target).__qualname__,
                    style="heading3",
                ),
                rio.Spacer(),
                *header_accessories,
                margin_bottom=0.2,
                spacing=0.5,
            ),
            row_index,
            0,
            width=5,
        )
        row_index += 1

        # Which file/line was this component instantiated from?
        file, line = target._creator_stackframe_

        try:
            file = file.relative_to(Path.cwd())
        except ValueError:
            pass

        result.add(
            rio.Text(
                f"{file} line {line}",
                style="dim",
                justify="left",
            ),
            row_index,
            0,
            width=5,
        )

        row_index_before_properties = row_index
        row_index += 1

        # Custom properties
        #
        # Make sure to skip any which already have custom tailored cells
        debug_details = target._get_debug_details()
        for prop_name, prop_value in debug_details.items():
            # Some values have special handling below
            if prop_name in (
                "key",
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
            value_limit = 30
            prop_str = repr(prop_value)

            if len(prop_str) > value_limit:
                prop_str = prop_str[: value_limit - 1] + "…"

            add_cell(prop_name, 0, True)
            add_cell(prop_str, 1, False, width=4)
            row_index += 1

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

            # Spacing to separate the table from the rest
            row_index += 1

            # Header
            result.add(
                rio.Text("width", style="dim", justify="left"), row_index, 1
            )
            result.add(
                rio.Text("height", style="dim", justify="left"), row_index, 2
            )
            row_index += 1

            # The size as specified in Python
            add_cell("python", 0, True)
            add_cell(py_width_str, 1, False)
            add_cell(py_height_str, 2, False)
            row_index += 1

            # The component's natural size
            add_cell("natural", 0, True)
            add_cell(str(round(self.component_natural_width, 2)), 1, False)
            add_cell(str(round(self.component_natural_height, 2)), 2, False)
            row_index += 1

            # The component's allocated size
            add_cell("allocated", 0, True)
            add_cell(str(round(self.component_allocated_width, 2)), 1, False)
            add_cell(str(round(self.component_allocated_height, 2)), 2, False)
            row_index += 1

            # More spacing
            row_index += 1

        # Margins
        (
            margin_left,
            margin_top,
            margin_right,
            margin_bottom,
        ) = self._get_effective_margins()

        single_x_margin = margin_left == margin_right
        single_y_margin = margin_top == margin_bottom

        if single_x_margin and single_y_margin:
            add_cell("margin", 0, True)
            add_cell(str(margin_left), 1, False)
            row_index += 1

        else:
            if single_x_margin:
                add_cell("margin_x", 0, True)
                add_cell(str(margin_left), 1, False)

            else:
                add_cell("margin_left", 0, True)
                add_cell(str(margin_left), 1, False)

                add_cell("margin_right", 2, True)
                add_cell(str(margin_right), 3, False)

            row_index += 1

            if single_y_margin:
                add_cell("margin_y", 0, True)
                add_cell(str(margin_top), 1, False)

            else:
                add_cell("margin_top", 0, True)
                add_cell(str(margin_top), 1, False)

                add_cell("margin_bottom", 2, True)
                add_cell(str(margin_bottom), 3, False)

            row_index += 1

        # Alignment
        if "align_x" in debug_details or "align_y" in debug_details:
            add_cell("align_x", 0, True)
            add_cell(str(debug_details.get("align_x", "-")), 1, False)

            add_cell("align_y", 2, True)
            add_cell(str(debug_details.get("align_y", "-")), 3, False)
            row_index += 1

        # Link to docs
        if type(target)._rio_builtin_:
            docs_url = rio.docs.build_documentation_url(type(target).__name__)
            link_color = self.session.theme.secondary_color

            result.add(
                rio.Link(
                    rio.Row(
                        rio.Icon("material/library-books", fill=link_color),
                        rio.Text("Docs", style=rio.TextStyle(fill=link_color)),
                        spacing=0.5,
                        align_x=0,
                    ),
                    docs_url,
                    # TODO: Support icons in links
                    open_in_new_tab=True,
                    margin_top=0.2,
                ),
                row_index,
                0,
                width=2,
            )
            row_index += 1

        # Push all of the content to the left. This could be done by aligning
        # the entire Grid, but that would ellipsize some long texts. Instead,
        # add a Spacer into a fifth column, which will take up any unused space.
        result.add(
            rio.Spacer(height=0),
            row_index - 1,
            4,
        )
        # result.add(
        #     layout_preview.LayoutPreview(component=target),
        #     row_index_before_properties + 1,
        #     4,
        #     height=row_index - row_index_before_properties,
        # )

        # Done
        return result
