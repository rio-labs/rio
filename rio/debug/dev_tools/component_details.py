from pathlib import Path
from typing import *  # type: ignore

import rio
import rio.docs

from ... import utils
from . import layout_preview

try:
    RIO_PATH = Path(rio.__file__).parent
except Exception:
    # Use a dummy path. It doesn't really matter, as long as it doesn't crash
    # `Path.is_relative_to`
    RIO_PATH = Path.cwd() / "rio"


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
        (allocation,) = await self.session._get_component_layouts(
            [component_id]
        )

        # If the current component has changed while the values were fetched,
        # don't update the state
        if self.component_id != component_id:
            return

        # Publish the results
        self.component_natural_width = allocation.natural_width
        self.component_natural_height = allocation.natural_height
        self.component_allocated_width = allocation.allocated_width
        self.component_allocated_height = allocation.allocated_height

    def _get_effective_margins(
        self, target: rio.Component
    ) -> Tuple[float, float, float, float]:
        return (
            utils.first_non_null(
                target.margin_left,
                target.margin_x,
                target.margin,
                0,
            ),
            utils.first_non_null(
                target.margin_top,
                target.margin_y,
                target.margin,
                0,
            ),
            utils.first_non_null(
                target.margin_right,
                target.margin_x,
                target.margin,
                0,
            ),
            utils.first_non_null(
                target.margin_bottom,
                target.margin_y,
                target.margin,
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

        debug_details = target._get_debug_details()

        return rio.Column(
            self._create_header(target),
            *self._create_instantiation_info(target),
            self._create_layout_details(target, debug_details),
            *self._create_extra_details(debug_details),
            # self._create_layout_revealer(target),
            spacing=0.2,
        )

    def _create_header(self, target: rio.Component) -> rio.Component:
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

        # Link to docs
        if type(target)._rio_builtin_:
            docs_url = rio.docs.build_documentation_url(type(target).__name__)
            link_color = self.session.theme.secondary_color

            docs_link = [
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
                    margin_left=0.5,
                ),
            ]
        else:
            docs_link = []

        return rio.Row(
            rio.Text(
                type(target).__qualname__,
                style="heading3",
            ),
            rio.Spacer(),
            *header_accessories,
            *docs_link,
            spacing=0.5,
        )

    def _create_instantiation_info(
        self, target: rio.Component
    ) -> Iterable[rio.Component]:
        # Which file/line was this component instantiated from?
        file, line = target._creator_stackframe_

        # If it was instantiated somewhere in the rio internals, don't show it
        if file.is_relative_to(RIO_PATH):
            return

        try:
            file = file.relative_to(Path.cwd())
        except ValueError:
            pass

        yield rio.Text(
            f"{file} line {line}",
            style="dim",
            justify="left",
        )

    def _create_layout_details(
        self, target: rio.Component, debug_details: dict[str, Any]
    ) -> rio.Component:
        # Create a grid with all the details
        grid = DetailsGrid()

        # Add some extra spacing
        grid.row += 1

        # Margins
        (
            margin_left,
            margin_top,
            margin_right,
            margin_bottom,
        ) = self._get_effective_margins(target)

        single_x_margin = margin_left == margin_right
        single_y_margin = margin_top == margin_bottom

        if single_x_margin and single_y_margin:
            grid.add_label("margin", column=0)
            grid.add_value(str(margin_left), column=1)

            grid.row += 1

        else:
            if single_x_margin:
                grid.add_label("margin_x", column=0)
                grid.add_value(str(margin_left), column=1)

            else:
                grid.add_label("margin_left", column=0)
                grid.add_value(str(margin_left), column=1)

                grid.add_label("margin_right", column=2)
                grid.add_value(str(margin_right), column=3)

            grid.row += 1

            if single_y_margin:
                grid.add_label("margin_y", column=0)
                grid.add_value(str(margin_top), column=1)

            else:
                grid.add_label("margin_top", column=0)
                grid.add_value(str(margin_top), column=1)

                grid.add_label("margin_bottom", column=2)
                grid.add_value(str(margin_bottom), column=3)

            grid.row += 1

        # Alignment
        if "align_x" in debug_details or "align_y" in debug_details:
            grid.add_label("align_x", column=0)
            grid.add_value(str(debug_details.get("align_x", "-")), column=1)

            grid.add_label("align_y", column=2)
            grid.add_value(str(debug_details.get("align_y", "-")), column=3)

            grid.row += 1

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
            grid.row += 1

            # Header
            grid.add_label("width", column=1)
            grid.add_label("height", column=2)
            grid.row += 1

            # The size as specified in Python
            grid.add_label("python", column=0)
            grid.add_value(py_width_str, column=1)
            grid.add_value(py_height_str, column=2)
            grid.row += 1

            # The component's natural size
            grid.add_label("natural", column=0)
            grid.add_value(
                str(round(self.component_natural_width, 2)), column=1
            )
            grid.add_value(
                str(round(self.component_natural_height, 2)), column=2
            )
            grid.row += 1

            # The component's allocated size
            grid.add_label("allocated", column=0)
            grid.add_value(
                str(round(self.component_allocated_width, 2)), column=1
            )
            grid.add_value(
                str(round(self.component_allocated_height, 2)), column=2
            )
            grid.row += 1

        # Push all of the content to the left. This could be done by aligning
        # the entire Grid, but that would ellipsize some long texts. Instead,
        # add a Spacer into a fifth column, which will take up any unused space.
        grid.add(
            rio.Spacer(height=0),
            column=5,
        )

        # Done
        return grid.as_rio_component()

    def _create_extra_details(
        self,
        debug_details: dict[str, Any],
    ) -> Iterable[rio.Component]:
        grid = DetailsGrid()

        # Custom properties
        #
        # Make sure to skip any which already have custom tailored cells
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
            grid.add_row(prop_name, repr(prop_value))

        if grid.row > 0:
            yield rio.Revealer(
                "More Attributes",
                grid.as_rio_component(),
                # header_style="heading3",
            )

    def _create_layout_revealer(self, target) -> rio.Component:
        return rio.Revealer(
            "Layout",
            layout_preview.LayoutPreview(component=target),
            header_style="heading3",
        )


class DetailsGrid:
    def __init__(self):
        self.grid = rio.Grid(row_spacing=0.5, column_spacing=0.5)
        self.row = 0
        self.max_column = 0

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
        width: int = 1,
    ) -> None:
        self.add(
            rio.Text(
                text,
                style="dim",
                justify="right",
            ),
            row=row,
            column=column,
            width=width,
        )

    def add_value(
        self,
        value: str,
        *,
        row: int | None = None,
        column: int,
        width: int = 1,
        ellipsize: bool = False,
    ) -> None:
        self.add(
            rio.Text(
                value,
                justify="left",
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

        self.max_column = max(self.max_column, column)

    def as_rio_component(self) -> rio.Component:
        return self.grid
