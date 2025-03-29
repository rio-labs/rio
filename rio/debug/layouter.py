from __future__ import annotations

import functools
import json
import sys
import typing as t

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

import rio
import rio.components.fundamental_component
import rio.components.root_components
from rio.data_models import UnittestComponentLayout

from .. import serialization

R = t.TypeVar("R")
P = t.ParamSpec("P")


# These components pass on the entirety of the available space to their
# children
FULL_SIZE_SINGLE_CONTAINERS: set[type[rio.Component]] = {
    rio.Card,
    rio.CustomListItem,
    rio.KeyEventListener,
    rio.Link,
    rio.MouseEventListener,
    rio.Rectangle,
    rio.Slideshow,
    rio.Stack,
    rio.Switcher,
}


def specialized(func: t.Callable[P, R]) -> t.Callable[P, R]:
    """
    Decorator that defers to a specialized method if one exists. If none is
    found, calls the original method.

    For example, consider a method called `foo`. If the function is called with
    a `rio.Row` instance as `self`, this will call `foo_Row` if it exists, and
    `foo` otherwise.
    """

    def result(self, component, *args, **kwargs) -> t.Any:
        # First, check if a specialized method for this component exists
        try:
            method = getattr(
                self,
                f"{func.__name__}_{type(component).__name__}",
            )
        except AttributeError:
            # Special case: A lot of containers behave in the same way - they pass
            # on all space. Avoid having to implement them all separately.
            if type(component) in FULL_SIZE_SINGLE_CONTAINERS or not isinstance(
                component,
                rio.components.fundamental_component.FundamentalComponent,
            ):
                method = getattr(self, f"{func.__name__}_SingleContainer")
            else:
                # If all else fails, use the default implementation
                method = functools.partial(func, self)

        return method(component, *args, **kwargs)  # type: ignore (wtf?)

    return result  # type: ignore


def _linear_container_get_major_axis_natural_size(
    child_requested_sizes: list[float],
    spacing: float,
    proportions: None | t.Literal["homogeneous"] | t.Sequence[float],
) -> float:
    # Spacing
    result = spacing * (len(child_requested_sizes) - 1)

    # Children
    #
    # No proportions
    if proportions is None:
        for child_requested_size in child_requested_sizes:
            result += child_requested_size

    # Proportions
    else:
        if proportions == "homogeneous":
            proportions = [1] * len(child_requested_sizes)
        else:
            proportions = list(proportions)

        # Find the width of 1 unit of proportions
        width_per_proportion = 0

        for child_size, proportion in zip(child_requested_sizes, proportions):
            width_per_proportion = max(
                width_per_proportion,
                child_size / proportion,
            )

        # Request the correct amount of space
        result += width_per_proportion * sum(proportions)

    return result


def _linear_container_get_major_axis_allocated_sizes(
    container_allocated_size: float,
    child_requested_sizes: list[float],
    child_growers: list[bool],
    spacing: float,
    proportions: None | t.Literal["homogeneous"] | t.Sequence[float],
) -> list[tuple[float, float]]:
    starts_and_sizes: list[tuple[float, float]] = []

    # Allow the code below to assume there is at least one child
    if not child_requested_sizes:
        return []

    # No proportions
    if proportions is None:
        cur_x = 0

        # Prepare for superfluous space
        additional_space = (
            container_allocated_size
            - sum(child_requested_sizes)
            - spacing * (len(child_requested_sizes) - 1)
        )

        n_growers = sum(child_growers)

        if n_growers == 0:
            additional_space_per_component = additional_space / len(
                child_requested_sizes
            )
            additional_space_per_grower = 0
        else:
            additional_space_per_component = 0
            additional_space_per_grower = additional_space / n_growers

        for child_requested_size, child_grow in zip(
            child_requested_sizes, child_growers
        ):
            # Determine how much space to pass on
            child_allocated_size = (
                child_requested_size + additional_space_per_component
            )

            if child_grow:
                child_allocated_size += additional_space_per_grower

            # Store the result
            starts_and_sizes.append((cur_x, child_allocated_size))
            cur_x += child_allocated_size + spacing

    # Proportions
    else:
        if proportions == "homogeneous":
            proportions = [1] * len(child_requested_sizes)
        else:
            proportions = list(proportions)

        # Find the width of 1 unit of proportions
        available_space = container_allocated_size - spacing * (
            len(child_requested_sizes) - 1
        )
        width_per_proportion = available_space / sum(proportions)

        # Pass on the correct amount of space
        cur_x = 0

        for proportion in proportions:
            starts_and_sizes.append((cur_x, width_per_proportion * proportion))
            cur_x += width_per_proportion * proportion + spacing

    # Done
    return starts_and_sizes


def calculate_alignment(
    allocated_outer_size: float,
    requested_inner_size: float,
    margin_start: float,
    margin_end: float,
    align: float | None,
) -> tuple[float, float]:
    # If no alignment is specified pass on all space
    if align is None:
        return margin_start, allocated_outer_size - margin_start - margin_end

    # If a margin is specified, only pass on the minimum amount of space and
    # distribute superfluous space
    additional_space = (
        allocated_outer_size - requested_inner_size - margin_start - margin_end
    )
    return margin_start + additional_space * align, requested_inner_size


def iter_direct_tree_children(
    component: rio.Component,
) -> t.Iterable[rio.Component]:
    """
    Iterates over the children of a component. In particular, the children which
    are part of the component tree, rather than those stored in the components
    attributes.
    """

    # Fundamental components can have any number of children
    if isinstance(
        component,
        rio.components.fundamental_component.FundamentalComponent,
    ):
        yield from component._iter_direct_and_indirect_child_containing_attributes_(
            include_self=False,
            recurse_into_high_level_components=True,
        )

    # High level components have a single child: their build result
    else:
        yield component._build_data_.build_result  # type: ignore


class Layouter:
    session: rio.Session

    window_width: float
    window_height: float

    # Map components to their layouts. One for client-side, one for server-side.
    _layouts_should: dict[int, UnittestComponentLayout]
    _layouts_are: dict[int, UnittestComponentLayout]

    # Function to filter uninteresting components. If this returns `False` for a
    # given component, that component and all of its children are ignored.
    _filter: t.Callable[[rio.Component], bool]

    # All components in the session, ordered such that each parent appears
    # before its children.
    _ordered_components: list[rio.Component]

    # Construction of this class is asynchronous. Make sure nobody does anything
    # silly.
    def __init__(self) -> None:
        raise TypeError(
            "Creating this class is asynchronous. Use the `create` method instead."
        )

    @staticmethod
    async def create(
        session: rio.Session,
        *,
        filter: t.Callable[[rio.Component], bool] = lambda _: True,
    ) -> Layouter:
        # Create a new instance
        self = Layouter.__new__(Layouter)
        self.session = session
        self._filter = filter

        # Get a sorted list of components. Each parent appears before its
        # children.
        self._ordered_components = list(
            self._get_toposorted(self.session._high_level_root_component)
        )

        # Fetch client-side information. This includes things such as the window
        # size and the natural size of components.
        #
        # While it is obviously the job of this class to calculate the layout,
        # there is little reason to re-implement the sizing logic of every
        # single component. Instead, fetch the natural sizes of leaf components,
        # and then make a pass over all parent components to determine the
        # correct layout.
        client_info = await self.session._get_unittest_client_layout_info()

        self.window_width = client_info.window_width
        self.window_height = client_info.window_height
        self._layouts_are = client_info.component_layouts

        # Make sure the received components match expectations
        component_ids_client = set(self._layouts_are.keys())
        component_ids_server = {c._id_ for c in self._ordered_components}

        missing_component_ids = component_ids_server - component_ids_client
        assert not missing_component_ids, missing_component_ids

        superfluous_component_ids = component_ids_client - component_ids_server
        assert not superfluous_component_ids, superfluous_component_ids

        # Compute server-side layouts
        self._layouts_should = {}
        self._compute_layouts_should(
            ordered_components=self._ordered_components,
        )

        # Done!
        return self

    def get_component_by_id(self, component_id: int) -> rio.Component:
        return self.session._weak_components_by_id[component_id]

    def get_layout_by_key(
        self,
        key: str | int,
    ) -> UnittestComponentLayout:
        """
        Returns the layout for the component with the given key.

        This function is intended to be used for additional tests after one has
        already checked that all attributes from layout-should and layout-are
        match. Because of this, this function simply returns the "should"
        variant of the layout, since it is bound to be identical to the other
        one anyway.

        However, the "should" variant has one advantage: Because it wasn't
        calculated by a browser with real-world pixels, any contained values are
        exact, meaning you can compare the values using a simple `==` rather
        than a fuzzy comparison.


        ## Raises

        `KeyError`: If there is no component with the given key.
        """

        for component in self._ordered_components:
            if component.key == key:
                return self._layouts_should[component._id_]

        raise KeyError(f"There is no component with key `{key}`")

    def _get_toposorted(
        self,
        root: rio.Component,
    ) -> t.Iterable[rio.Component]:
        """
        Returns the component, as well as all direct and indirect children. The
        results are ordered such that each parent appears before its children.
        """

        to_do: list[rio.Component] = [root]

        while to_do:
            # Track this component
            current = to_do.pop()
            yield current

            # Recur into children
            to_do.extend(iter_direct_tree_children(current))

    def _compute_layouts_should(
        self,
        ordered_components: list[rio.Component],
    ) -> None:
        # Pre-allocate layouts for each component. Also, ...
        #
        # 1. Update natural & requested width
        for component in reversed(ordered_components):
            layout_is = self._layouts_are[component._id_]
            layout_should = UnittestComponentLayout(
                natural_width=-1,
                natural_height=-1,
                requested_inner_width=-1,
                requested_inner_height=-1,
                requested_outer_width=-1,
                requested_outer_height=-1,
                allocated_outer_width=-1,
                allocated_outer_height=-1,
                allocated_inner_width=-1,
                allocated_inner_height=-1,
                left_in_viewport_outer=-1,
                top_in_viewport_outer=-1,
                left_in_viewport_inner=-1,
                top_in_viewport_inner=-1,
                parent_id=layout_is.parent_id,
                aux={},
            )
            self._layouts_should[component._id_] = layout_should

            # Let the component update its natural width
            self._update_natural_width(component)
            assert layout_should.natural_width >= -0.1, layout_should

            # Derive the requested width
            min_width = (
                component.min_width
                if isinstance(component.min_width, (int, float))
                else 0
            )
            layout_should.requested_inner_width = max(
                layout_should.natural_width, min_width
            )

            # Account for rounding errors
            layout_should.requested_outer_width = (
                layout_should.requested_inner_width
                + component._effective_margin_left_
                + component._effective_margin_right_
            )

        # 2. Update allocated width
        for component in ordered_components:
            layout = self._layouts_should[component._id_]

            left, width = calculate_alignment(
                allocated_outer_size=layout.allocated_outer_width,
                requested_inner_size=layout.requested_inner_width,
                margin_start=component._effective_margin_left_,
                margin_end=component._effective_margin_right_,
                align=component.align_x,
            )
            layout.left_in_viewport_inner = layout.left_in_viewport_outer + left
            layout.allocated_inner_width = width

            self._update_allocated_width(component)

        # 3. Update natural & requested height
        for component in reversed(ordered_components):
            layout_should = self._layouts_should[component._id_]

            # Let the component update its natural height
            self._update_natural_height(component)
            assert layout_should.natural_height >= -0.1, layout_should

            # Derive the requested height
            min_height = (
                component.min_height
                if isinstance(component.min_height, (int, float))
                else 0
            )
            layout_should.requested_inner_height = max(
                layout_should.natural_height, min_height
            )

            layout_should.requested_outer_height = (
                layout_should.requested_inner_height
                + component._effective_margin_top_
                + component._effective_margin_bottom_
            )

        # 4. Update allocated height
        for component in ordered_components:
            layout = self._layouts_should[component._id_]

            top, height = calculate_alignment(
                allocated_outer_size=layout.allocated_outer_height,
                requested_inner_size=layout.requested_inner_height,
                margin_start=component._effective_margin_top_,
                margin_end=component._effective_margin_bottom_,
                align=component.align_y,
            )
            layout.top_in_viewport_inner = layout.top_in_viewport_outer + top
            layout.allocated_inner_height = height

            self._update_allocated_height(component)

    @specialized
    def _update_natural_width(
        self,
        component: rio.Component,
    ) -> None:
        """
        Updates the natural width for the given component. This assumes that all
        children already have their requested width set.
        """

        # Default implementation: Trust the client
        layout_should = self._layouts_should[component._id_]
        layout_is = self._layouts_are[component._id_]

        layout_should.natural_width = layout_is.natural_width

    def _update_natural_width_Row(
        self,
        component: rio.Row,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id_]

        child_widths: list[float] = []

        for child in component._iter_referenced_components_():
            child_layout = self._layouts_should[child._id_]
            child_widths.append(child_layout.requested_outer_width)

        # Update
        layout.natural_width = _linear_container_get_major_axis_natural_size(
            child_requested_sizes=child_widths,
            spacing=component.spacing,
            proportions=component.proportions,
        )

    def _update_natural_width_Column(
        self,
        component: rio.Column,
    ) -> None:
        # Max of all Children
        layout = self._layouts_should[component._id_]
        layout.natural_width = 0

        for child in component._iter_referenced_components_():
            child_layout = self._layouts_should[child._id_]
            layout.natural_width = max(
                layout.natural_width, child_layout.requested_outer_width
            )

    def _update_natural_width_Overlay(
        self,
        component: rio.Overlay,
    ) -> None:
        layout = self._layouts_should[component._id_]
        layout.natural_width = 0

    def _update_natural_width_SingleContainer(
        self,
        component: rio.Component,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id_]
        layout.natural_width = 0

        # Pass on all space
        for child in iter_direct_tree_children(component):
            child_layout = self._layouts_should[child._id_]
            layout.natural_width = max(
                layout.natural_width,
                child_layout.requested_outer_width,
            )

    @specialized
    def _update_allocated_width(
        self,
        component: rio.Component,
    ) -> None:
        """
        Updates the allocated width of all of the component's children. This
        assumes that the component itself already has its requested width set.

        Furthermore, this also assigns the `left_in_viewport` attribute of all
        children.
        """
        # Default implementation: Trust the client
        for child in iter_direct_tree_children(component):
            child_layout_should = self._layouts_should[child._id_]
            child_layout_is = self._layouts_are[child._id_]

            child_layout_should.left_in_viewport_outer = (
                child_layout_is.left_in_viewport_outer
            )

            child_layout_should.allocated_outer_width = (
                child_layout_is.allocated_outer_width
            )

    def _update_allocated_width_HighLevelRootComponent(
        self,
        component: rio.components.root_components.HighLevelRootComponent,
    ) -> None:
        # Since the HighLevelRootComponent doesn't have a parent, it has to set
        # its own allocation
        layout_should = self._layouts_should[component._id_]
        layout_is = self._layouts_are[component._id_]

        # Because scrolling differs between debug mode and release mode (user
        # content scrolls vs browser scrolls), we'll just copy the values from
        # the client.
        layout_should.left_in_viewport_outer = layout_is.left_in_viewport_outer
        layout_should.left_in_viewport_inner = layout_is.left_in_viewport_inner

        layout_should.allocated_outer_width = layout_is.allocated_outer_width
        layout_should.allocated_inner_width = layout_is.allocated_inner_width

        # Then behave like a regular SingleContainer
        self._update_allocated_width_SingleContainer(component)

    def _update_allocated_width_Row(
        self,
        component: rio.Row,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id_]

        child_widths: list[float] = []

        for child in component._iter_referenced_components_():
            child_layout = self._layouts_should[child._id_]
            child_widths.append(child_layout.requested_outer_width)

        # Update
        starts_and_sizes = _linear_container_get_major_axis_allocated_sizes(
            container_allocated_size=layout.allocated_inner_width,
            child_requested_sizes=child_widths,
            child_growers=[
                child.grow_x
                for child in component._iter_referenced_components_()
            ],
            spacing=component.spacing,
            proportions=component.proportions,
        )

        for child, (left, width) in zip(
            component._iter_referenced_components_(), starts_and_sizes
        ):
            child_layout = self._layouts_should[child._id_]
            child_layout.left_in_viewport_outer = (
                layout.left_in_viewport_inner + left
            )
            child_layout.allocated_outer_width = width

    def _update_allocated_width_Column(
        self,
        component: rio.Column,
    ) -> None:
        layout = self._layouts_should[component._id_]

        for child in component._iter_referenced_components_():
            child_layout = self._layouts_should[child._id_]
            child_layout.left_in_viewport_outer = layout.left_in_viewport_inner
            child_layout.allocated_outer_width = layout.allocated_inner_width

    def _update_allocated_width_Overlay(
        self,
        component: rio.Overlay,
    ) -> None:
        child_layout = self._layouts_should[component.content._id_]
        child_layout.left_in_viewport_outer = 0
        child_layout.allocated_outer_width = self.window_width

    def _update_allocated_width_SingleContainer(
        self,
        component: rio.Component,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id_]

        # Pass on all space
        for child in iter_direct_tree_children(component):
            child_layout = self._layouts_should[child._id_]
            child_layout.left_in_viewport_outer = layout.left_in_viewport_inner
            child_layout.allocated_outer_width = layout.allocated_inner_width

    @specialized
    def _update_natural_height(
        self,
        component: rio.Component,
    ) -> None:
        """
        Updates the natural height for the given component. This assumes that
        all children already have their requested height set.
        """
        # Default implementation: Trust the client
        layout_should = self._layouts_should[component._id_]
        layout_is = self._layouts_are[component._id_]

        layout_should.natural_height = layout_is.natural_height

    def _update_natural_height_Row(
        self,
        component: rio.Row,
    ) -> None:
        # Max of all Children
        layout = self._layouts_should[component._id_]
        layout.natural_height = 0

        for child in component._iter_referenced_components_():
            child_layout = self._layouts_should[child._id_]
            layout.natural_height = max(
                layout.natural_height, child_layout.requested_outer_height
            )

    def _update_natural_height_Column(
        self,
        component: rio.Column,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id_]

        child_heights: list[float] = []

        for child in component._iter_referenced_components_():
            child_layout = self._layouts_should[child._id_]
            child_heights.append(child_layout.requested_outer_height)

        # Update
        layout.natural_height = _linear_container_get_major_axis_natural_size(
            child_requested_sizes=child_heights,
            spacing=component.spacing,
            proportions=component.proportions,
        )

    def _update_natural_height_Overlay(
        self,
        component: rio.Overlay,
    ) -> None:
        layout = self._layouts_should[component._id_]
        layout.natural_height = 0

    def _update_natural_height_SingleContainer(
        self,
        component: rio.Component,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id_]
        layout.natural_height = 0

        # Pass on all space
        for child in iter_direct_tree_children(component):
            child_layout = self._layouts_should[child._id_]
            layout.natural_height = max(
                layout.natural_height,
                child_layout.requested_outer_height,
            )

    @specialized
    def _update_allocated_height(
        self,
        component: rio.Component,
    ) -> None:
        """
        Updates the allocated height of all of the component's children. This
        assumes that the component itself already has its requested height set.

        Furthermore, this also assigns the `left_in_viewport` attribute of all
        children.
        """
        # Default implementation: Trust the client
        for child in iter_direct_tree_children(component):
            child_layout_should = self._layouts_should[child._id_]
            child_layout_is = self._layouts_are[child._id_]

            child_layout_should.allocated_outer_height = (
                child_layout_is.allocated_outer_height
            )

            child_layout_should.top_in_viewport_outer = (
                child_layout_is.top_in_viewport_outer
            )

    def _update_allocated_height_HighLevelRootComponent(
        self,
        component: rio.components.root_components.HighLevelRootComponent,
    ) -> None:
        # Since the HighLevelRootComponent doesn't have a parent, it has to set
        # its own allocation
        layout_should = self._layouts_should[component._id_]
        layout_is = self._layouts_are[component._id_]

        # Because scrolling differs between debug mode and release mode (user
        # content scrolls vs browser scrolls), we'll just copy the values from
        # the client.
        layout_should.top_in_viewport_outer = layout_is.top_in_viewport_outer
        layout_should.top_in_viewport_inner = layout_is.top_in_viewport_inner

        layout_should.allocated_outer_height = layout_is.allocated_outer_height
        layout_should.allocated_inner_height = layout_is.allocated_inner_height

        # Then behave like a regular SingleContainer
        self._update_allocated_height_SingleContainer(component)

    def _update_allocated_height_Row(
        self,
        component: rio.Row,
    ) -> None:
        layout = self._layouts_should[component._id_]

        for child in component._iter_referenced_components_():
            child_layout = self._layouts_should[child._id_]
            child_layout.top_in_viewport_outer = layout.top_in_viewport_inner
            child_layout.allocated_outer_height = layout.allocated_inner_height

    def _update_allocated_height_Column(
        self,
        component: rio.Column,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id_]

        child_heights: list[float] = []

        for child in component._iter_referenced_components_():
            child_layout = self._layouts_should[child._id_]
            child_heights.append(child_layout.requested_outer_height)

        # Update
        starts_and_sizes = _linear_container_get_major_axis_allocated_sizes(
            container_allocated_size=layout.allocated_inner_height,
            child_requested_sizes=child_heights,
            child_growers=[
                child.grow_y
                for child in component._iter_referenced_components_()
            ],
            spacing=component.spacing,
            proportions=component.proportions,
        )

        for child, (top, height) in zip(
            component._iter_referenced_components_(), starts_and_sizes
        ):
            child_layout = self._layouts_should[child._id_]
            child_layout.top_in_viewport_outer = (
                layout.top_in_viewport_inner + top
            )
            child_layout.allocated_outer_height = height

    def _update_allocated_height_Overlay(
        self,
        component: rio.Overlay,
    ) -> None:
        child_layout = self._layouts_should[component.content._id_]
        child_layout.top_in_viewport_outer = 0
        child_layout.allocated_outer_height = self.window_height

    def _update_allocated_height_SingleContainer(
        self,
        component: rio.Component,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id_]

        # Pass on all space
        for child in iter_direct_tree_children(component):
            child_layout = self._layouts_should[child._id_]
            child_layout.top_in_viewport_outer = layout.top_in_viewport_inner
            child_layout.allocated_outer_height = layout.allocated_inner_height

    def debug_dump_json(
        self,
        which: t.Literal["should", "are"],
        out: t.IO[str],
    ) -> None:
        """
        Dumps the layouts to a JSON file.
        """
        # Export the layouts to a JSON file
        layouts = (
            self._layouts_should if which == "should" else self._layouts_are
        )

        # Convert the class instances to JSON
        result: list[dict[str, t.Any]] = []

        def dump_recursive(component: rio.Component) -> None:
            # Honor the filter function
            if not self._filter(component):
                return

            # Build the subresult
            layout = layouts[component._id_]
            value_json = {
                "id": component._id_,
                "type": type(component).__name__,
                **serialization.json_serde.as_json(layout),  # type: ignore (definitely a dict)
            }

            # Round floats
            for key, value in value_json.items():
                if isinstance(value, float):
                    value_json[key] = round(value, 1)

            # Store the subresult
            result.append(value_json)

            # Chain to children
            for child in iter_direct_tree_children(component):
                dump_recursive(child)

        dump_recursive(self.session._high_level_root_component)

        # Write the result
        json.dump(
            result,
            out,
            indent=4,
        )

    def debug_draw(
        self,
        which: t.Literal["should", "are"],
        *,
        pixels_per_unit: float = 10,
    ) -> PIL.Image.Image:
        """
        Draws the layout of all components to a raster image.
        """

        # Set up
        image = PIL.Image.new(
            "RGB",
            (
                round(self.window_width * pixels_per_unit),
                round(self.window_height * pixels_per_unit),
            ),
            color="white",  # type: ignore
        )

        draw = PIL.ImageDraw.Draw(image)

        layouts = (
            self._layouts_should if which == "should" else self._layouts_are
        )

        # How deep is the deepest nesting?
        def get_nesting(component: rio.Component, level: int) -> int:
            result = level

            for child in iter_direct_tree_children(component):
                result = max(result, get_nesting(child, level + 1))

            return result

        n_layers = get_nesting(self.session._high_level_root_component, 1)

        # Draw all components recursively
        def draw_component(
            component: rio.Component,
            level: int,
        ) -> None:
            # Honor the filter function
            if not self._filter(component):
                return

            # Determine the color. The deeper the darker
            nesting_fraction = level / (n_layers + 1)
            color_8bit = round(255 * nesting_fraction)
            color = (color_8bit, color_8bit, color_8bit)

            # Draw the component
            layout = layouts[component._id_]

            rect_left = layout.left_in_viewport_inner * pixels_per_unit
            rect_top = layout.top_in_viewport_inner * pixels_per_unit
            rect_right = (
                layout.left_in_viewport_inner + layout.allocated_inner_width
            ) * pixels_per_unit
            rect_bottom = (
                layout.top_in_viewport_inner + layout.allocated_inner_height
            ) * pixels_per_unit

            rect_right = max(rect_right, rect_left)
            rect_bottom = max(rect_bottom, rect_top)

            draw.rectangle(
                (
                    rect_left,
                    rect_top,
                    rect_right,
                    rect_bottom,
                ),
                fill=color,
            )

            # Label it
            label_str = type(component).__name__
            font = PIL.ImageFont.load_default()

            text_width = draw.textlength(label_str, font=font)
            text_height = pixels_per_unit * 1.5

            draw.text(
                (
                    rect_left + (rect_right - rect_left - text_width) / 2,
                    rect_top + (rect_bottom - rect_top - text_height) / 2,
                ),
                label_str,
                fill="blue",
                font=font,
            )

            # Chain to children
            for child in iter_direct_tree_children(component):
                draw_component(child, level + 1)

        draw_component(self.session._high_level_root_component, 1)

        # Done
        return image

    def print_tree(self) -> None:
        out = sys.stdout

        def print_worker(component: rio.Component, indent: str) -> None:
            # Honor the filter function
            if not self._filter(component):
                out.write("<filtered>")
                out.write("\n")
                return

            # Print the component
            out.write(type(component).__name__)
            out.write("\n")

            # Chain to children
            children = list(iter_direct_tree_children(component))
            for ii, child in enumerate(children):
                if ii == len(children) - 1:
                    out.write(indent + " └─ ")
                    child_indent = "    "
                else:
                    out.write(indent + " ├─ ")
                    child_indent = " │  "

                print_worker(child, indent + child_indent)

        print_worker(self.session._high_level_root_component, "")
