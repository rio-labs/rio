from __future__ import annotations

import typing as t

import rio

from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = ["GraphEditor", "GraphStore"]


P = t.ParamSpec("P")


@t.final
class GraphStore:
    """
    ## Metadata

    `public`: False
    """

    def __init__(self) -> None:
        # The graph currently connected to the store. At any point in time there
        # can only be one graph connected to the store.
        #
        # It is the store's responsibility to keep JavaScript and Rio up-to-date
        # with any changes to the graph.
        self._graph: GraphEditor | None = None

        # All node instances currently in the graph
        self._nodes: list[rio.Component] = []

        # All as-of-yet uninstantiated nodes. Since nodes can only be
        # instantiated while in a `build` function, this list will be used to
        # instantiate all nodes when the graph is being (re-) built.
        self._uninstantiated_nodes: list[tuple[t.Callable, tuple, dict]] = []

    def _set_editor(self, editor: GraphEditor) -> list[rio.Component]:
        """
        Connects the graph editor to the store and returns the flat list of
        children of the graph. This list will be shared between the two and
        updated in-place as needed.

        If the store was already previously connected to another graph editor,
        it will disconnect from it first.
        """
        # Already connected to an editor?
        if self._graph is not None:
            self._graph.children = []

        # Connect to the new editor
        self._graph = editor
        return self._nodes

    def add_node(
        self,
        node_type: t.Callable[P, rio.Component],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        """
        Creates a node of the given type and adds it to the graph.
        """
        # Keep track of the node. It can't be instantiated yet, because Rio
        # components can only be created inside of `build` functions.
        self._uninstantiated_nodes.append((node_type, args, kwargs))

        # Tell the graph editor to rebuild
        if self._graph is not None:
            self._graph.force_refresh()


@t.final
class GraphEditor(FundamentalComponent):
    """
    ## Metadata

    `public`: False
    """

    children: list[rio.Component]

    def __init__(
        self,
        *children: rio.Component,
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
    ) -> None:
        super().__init__(
            key=key,
            margin=margin,
            margin_x=margin_x,
            margin_y=margin_y,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
            align_x=align_x,
            align_y=align_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
            accessibility_role=accessibility_role,
        )

        self.children = list(children)


GraphEditor._unique_id_ = "GraphEditor-builtin"
