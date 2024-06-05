from typing import *  # type: ignore

import rio.components.component_tree

from . import component_details, layout_subpage

MARGIN = 1


class TreePage(rio.Component):
    """
    This page displays all components in the app as an interactive tree.
    Components can be selected to view their details. This comes with a fair
    amount of complexity, since the page effectively switches between multiple
    views.
    """

    current_view: Literal["tree", "details", "layout"] = "tree"

    # This can be invalid. The component must deal with it.
    selected_component_id: int = -1

    def _switch_to_tree(self, _: rio.PressEvent) -> None:
        self.current_view = "tree"

    def _switch_to_details(self) -> None:
        self.current_view = "details"

    def _switch_to_layout(self) -> None:
        self.current_view = "layout"

    def _build_back_menu(self, label: str) -> rio.Component:
        return rio.MouseEventListener(
            rio.Rectangle(
                content=rio.Row(
                    rio.Icon(
                        "material/arrow-back",
                        width=2.2,
                        height=2.2,
                    ),
                    rio.Text(
                        label,
                        selectable=False,
                        style="heading2",
                        justify="left",
                        width="grow",
                    ),
                    spacing=1,
                    margin=MARGIN,
                ),
                fill=rio.Color.TRANSPARENT,
                hover_fill=self.session.theme.neutral_palette.background_active,
                ripple=True,
                cursor=rio.CursorStyle.POINTER,
                transition_time=0.1,
            ),
            on_press=self._switch_to_tree,
        )

    def _build_tree_view(self) -> rio.Component:
        return rio.Column(
            rio.Text(
                "Component Tree",
                style="heading2",
                margin_right=MARGIN,
                justify="left",
            ),
            rio.components.component_tree.ComponentTree(
                component_id=self.bind().selected_component_id,
                height="grow",
                # Note how there is no `margin_right` here. This is intentional
                # because the tree has an internal scroll bar which would look
                # silly if floating in space.
            ),
            # rio.Spacer(),
            rio.Button(
                "Details",
                icon="info",
                shape="rounded",
                on_press=self._switch_to_details,
                margin_right=MARGIN,
            ),
            rio.Button(
                "Layout",
                icon="space-dashboard",
                shape="rounded",
                on_press=self._switch_to_layout,
                margin_right=MARGIN,
            ),
            spacing=0.5,
            margin_left=MARGIN,
            margin_top=MARGIN,
            margin_bottom=MARGIN,
        )

    def _build_details_view(self) -> rio.Component:
        assert self.current_view == "details", self.current_view
        assert self.selected_component_id is not None

        # Get the target component
        try:
            target = self.session._weak_components_by_id[
                self.selected_component_id
            ]
            heading = type(target).__name__
        except KeyError:
            heading = "Component Details"

        # Delegate the hard work to another component
        return rio.Column(
            self._build_back_menu(heading),
            rio.ScrollContainer(
                component_details.ComponentDetails(
                    component_id=self.bind().selected_component_id,
                    on_switch_to_layout_view=self._switch_to_layout,
                    margin_right=MARGIN,
                    align_y=0,
                ),
                scroll_x="never",
                scroll_y="auto",
                margin_left=MARGIN,
                margin_bottom=MARGIN,
                height="grow",
            ),
        )

    def _build_layout_view(self) -> rio.Component:
        assert self.current_view == "layout", self.current_view
        assert self.selected_component_id is not None

        return rio.Column(
            self._build_back_menu("Layout"),
            rio.ScrollContainer(
                layout_subpage.LayoutSubpage(
                    component_id=self.bind().selected_component_id,
                    margin_right=MARGIN,
                    align_y=0,
                ),
                scroll_x="never",
                scroll_y="auto",
                margin_left=MARGIN,
                margin_top=MARGIN,
                margin_bottom=MARGIN,
                height="grow",
            ),
        )

    def build(self) -> rio.Component:
        if self.current_view == "tree":
            return self._build_tree_view()

        if self.current_view == "details":
            return self._build_details_view()

        if self.current_view == "layout":
            return self._build_layout_view()

        raise AssertionError("Unreachable")
