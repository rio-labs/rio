from __future__ import annotations

import json
from typing import *  # type: ignore
from typing import Iterable

import PIL.Image
import PIL.ImageDraw
import uniserde

import rio
import rio.components.fundamental_component
import rio.components.root_components
from rio.data_models import UnittestComponentLayout

R = TypeVar("R")
P = ParamSpec("P")


# These components pass on the entirety of the available space to their
# children
FULL_SIZE_SINGLE_CONTAINERS: set[type[rio.Component]] = {
    rio.Button,
    rio.Card,
    rio.Container,
    rio.CustomListItem,
    rio.KeyEventListener,
    rio.Link,
    rio.MouseEventListener,
    rio.PageView,
    rio.Rectangle,
    rio.Slideshow,
    rio.Stack,
    rio.Switcher,
}


def specialized(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator that defers to a specialized method if one exists. If none is
    found, calls the original method.

    For example, consider a method called `foo`. If the function is called with
    a `rio.Row` instance as `self`, this will call `foo_Row` if it exists, and
    `foo` otherwise.
    """

    def result(self, component, *args, **kwargs) -> Any:
        # Special case: A lot of containers behave in the same way - they pass
        # on all space. Avoid having to implement them all separately.
        if type(self) in FULL_SIZE_SINGLE_CONTAINERS:
            function_name = f"{func.__name__}_SingleContainer"
        else:
            function_name = f"{func.__name__}_{type(component).__name__}"

        # Delegate to a specialized method if it exists
        try:
            method = getattr(self, function_name)
        except AttributeError:
            return func(self, component, *args, **kwargs)  # type: ignore
        else:
            return method(component, *args, **kwargs)

    return result  # type: ignore


def _linear_container_get_major_axis_natural_size(
    child_requested_sizes: list[float],
    spacing: float,
) -> float:
    # Spacing
    result = spacing * (len(child_requested_sizes) - 1)

    # Children
    for child_requested_size in child_requested_sizes:
        result += child_requested_size

    return result


def _linear_container_get_major_axis_allocated_sizes(
    container_allocated_size: float,
    child_requested_sizes: list[float],
    spacing: float,
    proportions: None | Literal["homogeneous"] | Sequence[float],
) -> list[tuple[float, float]]:
    starts_and_sizes: list[tuple[float, float]] = []

    # No proportions
    if proportions is None:
        cur_x = 0

        # TODO: Superfluous Space + Growers

        for child_requested_size in child_requested_sizes:
            starts_and_sizes.append((cur_x, child_requested_size))
            cur_x += child_requested_size + spacing

    # Proportions
    else:
        raise NotImplementedError(
            f"TODO: Support proportions in linear containers"
        )

    # Done
    return starts_and_sizes


def iter_direct_tree_children(
    session: rio.Session,
    component: rio.Component,
) -> Iterable[rio.Component]:
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
        yield from component._iter_direct_children()

    # High level components have a single child: their build result
    else:
        build_data = session._weak_component_data_by_component[component]
        yield build_data.build_result


class Layouter:
    session: rio.Session

    window_width: float
    window_height: float

    # Map components to their layouts. One for client-side, one for server-side.
    _layouts_should: dict[int, UnittestComponentLayout]
    _layouts_are: dict[int, UnittestComponentLayout]

    # Construction of this class is asynchronous. Make sure nobody does anything silly.
    def __init__(self) -> None:
        raise TypeError(
            "Creating this class is asynchronous. Use the `create` method instead."
        )

    @staticmethod
    async def create(session: rio.Session) -> Layouter:
        # Create a new instance
        self = Layouter.__new__(Layouter)
        self.session = session

        # Get a sorted list of components. Each parent appears before its
        # children.
        ordered_components: list[rio.Component] = list(
            self._get_toposorted(self.session._root_component)
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
        component_ids_server = {c._id for c in ordered_components}

        missing_component_ids = component_ids_server - component_ids_client
        assert not missing_component_ids, missing_component_ids

        superfluous_component_ids = component_ids_client - component_ids_server
        assert not superfluous_component_ids, superfluous_component_ids

        # Compute server-side layouts
        self._layouts_should = {}
        self._compute_layouts_should(
            ordered_components=ordered_components,
        )

        # Done!
        return self

    def _get_toposorted(
        self,
        root: rio.Component,
    ) -> Iterable[rio.Component]:
        """
        Returns the component, as well as all direct and indirect children. The
        results are ordered such that each parent appears before its children.
        """

        to_do: list[rio.Component] = [root]

        while to_do:
            current = to_do.pop()
            yield current

            to_do.extend(iter_direct_tree_children(self.session, current))

    def _compute_layouts_should(
        self,
        ordered_components: list[rio.Component],
    ) -> None:
        # Pre-allocate layouts for each component. Also, ...
        #
        # 1. Update natural & requested width
        for component in reversed(ordered_components):
            layout_should = UnittestComponentLayout(
                left_in_viewport=-1,
                top_in_viewport=-1,
                natural_width=-1,
                natural_height=-1,
                requested_width=-1,
                requested_height=-1,
                allocated_width=-1,
                allocated_height=-1,
                aux={},
            )
            self._layouts_should[component._id] = layout_should

            # Let the component update its natural width
            self._update_natural_width(component)

            # Derive the requested width
            min_width = (
                component.width
                if isinstance(component.width, (int, float))
                else 0
            )
            layout_should.requested_width = max(
                layout_should.natural_width, min_width
            )

        # 2. Update allocated width
        root_layout = self._layouts_should[self.session._root_component._id]
        root_layout.left_in_viewport = 0
        root_layout.allocated_width = max(
            self.window_width, root_layout.requested_width
        )

        for component in ordered_components:
            self._update_allocated_width(component)

        # 3. Update natural & requested height
        for component in reversed(ordered_components):
            layout_should = self._layouts_should[component._id]

            # Let the component update its natural height
            self._update_natural_height(component)

            # Derive the requested height
            min_height = (
                component.height
                if isinstance(component.height, (int, float))
                else 0
            )
            layout_should.requested_height = max(
                layout_should.natural_height, min_height
            )

        # 4. Update allocated height
        root_layout.top_in_viewport = 0
        root_layout.allocated_height = max(
            self.window_height, root_layout.requested_height
        )

        for component in ordered_components:
            layout_should = self._layouts_should[component._id]
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
        layout_should = self._layouts_should[component._id]
        layout_is = self._layouts_are[component._id]

        layout_should.natural_width = layout_is.natural_width

    def _update_natural_width_Row(
        self,
        component: rio.Row,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id]

        child_widths: list[float] = []

        for child in component._iter_direct_children():
            child_layout = self._layouts_should[child._id]
            child_widths.append(child_layout.requested_width)

        # Update
        layout.natural_width = _linear_container_get_major_axis_natural_size(
            child_requested_sizes=child_widths,
            spacing=component.spacing,
        )

    def _update_natural_width_Column(
        self,
        component: rio.Column,
    ) -> None:
        # Max of all Children
        layout = self._layouts_should[component._id]
        layout.natural_width = 0

        for child in component._iter_direct_children():
            child_layout = self._layouts_should[child._id]
            layout.natural_width = max(
                layout.natural_width, child_layout.requested_width
            )

    def _update_natural_width_Overlay(
        self,
        component: rio.Overlay,
    ) -> None:
        layout = self._layouts_should[component._id]
        layout.natural_width = 0

    def _update_natural_width_SingleContainer(
        self,
        component: rio.Component,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id]

        children = list(component._iter_direct_children())
        assert len(children) == 1
        child = children[0]
        child_layout = self._layouts_should[child._id]

        # Pass on all space
        layout.natural_width = child_layout.requested_width

    @specialized
    def _update_allocated_width(
        self,
        component: rio.Component,
    ) -> None:
        """
        Updates the allocated width of all of the component's children. This
        assumes that the component itself already has its requested width set.
        """
        # Default implementation: Trust the client
        for child in iter_direct_tree_children(self.session, component):
            child_layout_should = self._layouts_should[child._id]
            child_layout_is = self._layouts_are[child._id]

            child_layout_should.allocated_width = (
                child_layout_is.allocated_width
            )

    def _update_allocated_width_Row(
        self,
        component: rio.Row,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id]

        child_widths: list[float] = []

        for child in component._iter_direct_children():
            child_layout = self._layouts_should[child._id]
            child_widths.append(child_layout.requested_width)

        # Update
        starts_and_sizes = _linear_container_get_major_axis_allocated_sizes(
            container_allocated_size=layout.allocated_width,
            child_requested_sizes=child_widths,
            spacing=component.spacing,
            proportions=component.proportions,
        )

        for child, (left, width) in zip(
            component._iter_direct_children(), starts_and_sizes
        ):
            child_layout = self._layouts_should[child._id]
            child_layout.left_in_viewport = layout.left_in_viewport + left
            child_layout.allocated_width = width

    def _update_allocated_width_Column(
        self,
        component: rio.Column,
    ) -> None:
        layout = self._layouts_should[component._id]

        for child in component._iter_direct_children():
            child_layout = self._layouts_should[child._id]
            child_layout.left_in_viewport = layout.left_in_viewport
            child_layout.allocated_width = layout.allocated_width

    def _update_allocated_width_Overlay(
        self,
        component: rio.Overlay,
    ) -> None:
        child_layout = self._layouts_should[component.content._id]
        child_layout.left_in_viewport = 0
        child_layout.allocated_width = self.window_width

    def _update_allocated_width_SingleContainer(
        self,
        component: rio.Component,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id]

        children = list(component._iter_direct_children())
        assert len(children) == 1
        child = children[0]
        child_layout = self._layouts_should[child._id]

        # Pass on all space
        child_layout.left_in_viewport = layout.left_in_viewport
        child_layout.allocated_width = layout.allocated_width

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
        layout_should = self._layouts_should[component._id]
        layout_is = self._layouts_are[component._id]

        layout_should.natural_height = layout_is.natural_height

    def _update_natural_height_Row(
        self,
        component: rio.Row,
    ) -> None:
        # Max of all Children
        layout = self._layouts_should[component._id]
        layout.natural_height = 0

        for child in component._iter_direct_children():
            child_layout = self._layouts_should[child._id]
            layout.natural_height = max(
                layout.natural_height, child_layout.requested_height
            )

    def _update_natural_height_Column(
        self,
        component: rio.Column,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id]

        child_heights: list[float] = []

        for child in component._iter_direct_children():
            child_layout = self._layouts_should[child._id]
            child_heights.append(child_layout.requested_height)

        # Update
        layout.natural_height = _linear_container_get_major_axis_natural_size(
            child_requested_sizes=child_heights,
            spacing=component.spacing,
        )

    def _update_natural_height_Overlay(
        self,
        component: rio.Overlay,
    ) -> None:
        layout = self._layouts_should[component._id]
        layout.natural_height = 0

    def _update_natural_height_SingleContainer(
        self,
        component: rio.Component,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id]

        children = list(component._iter_direct_children())
        assert len(children) == 1
        child = children[0]
        child_layout = self._layouts_should[child._id]

        # Pass on all space
        layout.natural_height = child_layout.requested_height

    @specialized
    def _update_allocated_height(
        self,
        component: rio.Component,
    ) -> None:
        """
        Updates the allocated height of all of the component's children. This
        assumes that the component itself already has its requested height set.

        Furthermore, this also assigns the `left_in_viewport` and
        `top_in_viewport` attributes of all children.
        """
        # Default implementation: Trust the client
        for child in iter_direct_tree_children(self.session, component):
            child_layout_should = self._layouts_should[child._id]
            child_layout_is = self._layouts_are[child._id]

            child_layout_should.allocated_height = (
                child_layout_is.allocated_height
            )
            child_layout_should.left_in_viewport = (
                child_layout_is.left_in_viewport
            )
            child_layout_should.top_in_viewport = (
                child_layout_is.top_in_viewport
            )

    def _update_allocated_height_Row(
        self,
        component: rio.Row,
    ) -> None:
        layout = self._layouts_should[component._id]

        for child in component._iter_direct_children():
            child_layout = self._layouts_should[child._id]
            child_layout.top_in_viewport = layout.top_in_viewport
            child_layout.allocated_height = layout.allocated_height

    def _update_allocated_height_Column(
        self,
        component: rio.Column,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id]

        child_heights: list[float] = []

        for child in component._iter_direct_children():
            child_layout = self._layouts_should[child._id]
            child_heights.append(child_layout.requested_height)

        # Update
        starts_and_sizes = _linear_container_get_major_axis_allocated_sizes(
            container_allocated_size=layout.allocated_height,
            child_requested_sizes=child_heights,
            spacing=component.spacing,
            proportions=component.proportions,
        )

        for child, (top, height) in zip(
            component._iter_direct_children(), starts_and_sizes
        ):
            child_layout = self._layouts_should[child._id]
            child_layout.top_in_viewport = layout.top_in_viewport + top
            child_layout.allocated_height = height

    def _update_allocated_height_Overlay(
        self,
        component: rio.Overlay,
    ) -> None:
        child_layout = self._layouts_should[component.content._id]
        child_layout.top_in_viewport = 0
        child_layout.allocated_height = self.window_height

    def _update_allocated_height_SingleContainer(
        self,
        component: rio.Component,
    ) -> None:
        # Prepare
        layout = self._layouts_should[component._id]

        children = list(component._iter_direct_children())
        assert len(children) == 1
        child = children[0]
        child_layout = self._layouts_should[child._id]

        # Pass on all space
        child_layout.top_in_viewport = layout.top_in_viewport
        child_layout.allocated_height = layout.allocated_height

    def debug_dump_json(
        self,
        which: Literal["should", "are"],
        out: IO[str],
    ) -> None:
        """
        Dumps the layouts to a JSON file.
        """
        # Export the layouts to a JSON file
        layouts = (
            self._layouts_should if which == "should" else self._layouts_are
        )

        # Convert the class instances to JSON
        result = {}

        layouts = list(layouts.items())
        layouts.sort(key=lambda x: x[0])

        for key, value_class in layouts:
            component = self.session._weak_components_by_id[key]
            value_json = {
                "type": type(component).__name__,
                **uniserde.as_json(value_class),
            }

            for key2, value in value_json.items():
                if isinstance(value, float):
                    value_json[key2] = round(value, 1)

            result[key] = value_json

        json.dump(
            result,
            out,
            indent=4,
        )

    def debug_draw(
        self,
        which: Literal["should", "are"],
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
            color="white",
        )

        draw = PIL.ImageDraw.Draw(image)

        layouts = (
            self._layouts_should if which == "should" else self._layouts_are
        )

        # How deep is the deepest nesting?
        def get_nesting(component: rio.Component, level: int) -> int:
            result = level

            for child in iter_direct_tree_children(self.session, component):
                result = max(result, get_nesting(child, level + 1))

            return result

        n_layers = get_nesting(self.session._root_component, 1)

        # Draw all components recursively
        def draw_component(
            component: rio.Component,
            level: int,
        ) -> None:
            # Determine the color. The deeper the darker
            nesting_fraction = level / (n_layers + 1)
            color_8bit = round(255 * nesting_fraction)
            color = (color_8bit, color_8bit, color_8bit)

            # Draw the component
            layout = layouts[component._id]
            draw.rectangle(
                (
                    layout.left_in_viewport * pixels_per_unit,
                    layout.top_in_viewport * pixels_per_unit,
                    (layout.left_in_viewport + layout.allocated_width)
                    * pixels_per_unit,
                    (layout.top_in_viewport + layout.allocated_height)
                    * pixels_per_unit,
                ),
                fill=color,
            )

            # Chain to children
            for child in iter_direct_tree_children(self.session, component):
                draw_component(child, level + 1)

        draw_component(self.session._root_component, 1)

        # Done
        return image
