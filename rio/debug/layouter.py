from __future__ import annotations

import json
from typing import *  # type: ignore
from typing import Iterable

import PIL.Image
import PIL.ImageDraw
import uniserde

import rio
import rio.components.fundamental_component
from rio.data_models import UnittestComponentLayout

R = TypeVar("R")
P = ParamSpec("P")


def specialized(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator that defers to a specialized method if one exists. If none is
    found, calls the original method.

    For example, consider a method called `foo`. If the function is called with
    a `rio.Row` instance as `self`, this will call `foo_Row` if it exists, and
    `foo` otherwise.
    """

    def result(self, *args, **kwargs) -> Any:
        try:
            method = getattr(self, f"{func.__name__}_{type(self).__name__}")
        except AttributeError:
            return func(self, *args, **kwargs)  # type: ignore
        else:
            return method(*args, **kwargs)

    return result  # type: ignore


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

            # Fundamental components can have any number of children
            if isinstance(
                current,
                rio.components.fundamental_component.FundamentalComponent,
            ):
                to_do.extend(current._iter_direct_children())

            # High level components have a single child: their build result
            else:
                build_data = self.session._weak_component_data_by_component[
                    current
                ]
                to_do.append(build_data.build_result)

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
            layout_should = self._layouts_should[component._id]
            self._update_allocated_width(component)

        # 3. Update natural & requested height
        for component in ordered_components:
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

    # def _update_natural_width_Row(
    #     self,
    #     component: rio.Row,
    # ) -> None:
    #     # Spacing
    #     layout = self._layouts_should[component._id]
    #     layout.natural_width = component.spacing * (len(component.children) - 1)

    #     # Children
    #     for child in component._iter_direct_children():
    #         child_layout = self._layouts_should[child._id]
    #         layout.natural_width += child_layout.requested_width

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
        for child in component._iter_direct_children():
            child_layout_should = self._layouts_should[child._id]
            child_layout_is = self._layouts_are[child._id]

            child_layout_should.allocated_width = (
                child_layout_is.allocated_width
            )

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

    # def _update_natural_height_Row(
    #     self,
    #     component: rio.Row,
    # ) -> None:
    #     # Spacing
    #     layout = self._layouts_should[component._id]
    #     layout.natural_height = 0

    #     # Children
    #     for child in component._iter_direct_children():
    #         child_layout = self._layouts_should[child._id]
    #         layout.natural_height = max(
    #             layout.natural_height, child_layout.requested_height
    #         )

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
        for child in component._iter_direct_children():
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
                if isinstance(key2, float):
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
