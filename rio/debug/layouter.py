from typing import Iterable

import rio
import rio.components.fundamental_component
from rio.data_models import UnittestComponentLayout


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
    async def create(
        session: rio.Session,
    ) -> None:
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
        client_info = await self.session._get_client_layout_info()

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
        self._compute_layouts_should(
            ordered_components=ordered_components,
        )

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
            layout = UnittestComponentLayout(
                left_in_parent=-1,
                top_in_parent=-1,
                natural_width=-1,
                natural_height=-1,
                requested_width=-1,
                requested_height=-1,
                allocated_width=-1,
                allocated_height=-1,
                aux={},
            )

            self._layouts_should[component._id] = layout

            self._update_natural_width(component, layout)

            min_width = (
                component.width
                if isinstance(component.width, (int, float))
                else 0
            )
            layout.requested_width = max(layout.natural_width, min_width)

        # 2. Update allocated width
        root_layout = self._layouts_should[self.component._id]
        root_layout.allocated_width = self.window_width
        root_layout.allocated_height = self.window_height

        for component in ordered_components:
            layout = self._layouts_should[component._id]
            self._update_allocated_width(component, layout)

        # 3. Update natural & requested height
        for component in ordered_components:
            layout = self._layouts_should[component._id]

            self._update_natural_height(component, layout)

            min_height = (
                component.height
                if isinstance(component.height, (int, float))
                else 0
            )
            layout.requested_height = max(layout.natural_height, min_height)

        # 4. Update allocated height
        for component in ordered_components:
            layout = self._layouts_should[component._id]
            self._update_allocated_height(component, layout)
