import typing as t

import rio.debug.dev_tools.component_picker
import rio.debug.dev_tools.component_tree

from . import component_attributes, layout_subpage

MARGIN = 1


class TreePage(rio.Component):
    """
    This page displays all components in the app as an interactive tree.
    Components can be selected to view their details. This comes with a fair
    amount of complexity, since the page effectively switches between multiple
    views.
    """

    current_view: t.Literal["tree", "attributes", "layout"] = "tree"

    # This can be invalid. The component must deal with it.
    selected_component_id: int = -1

    def _switch_to_tree(self, _: rio.PointerEvent) -> None:
        self.current_view = "tree"

    def _switch_to_details(self) -> None:
        self.current_view = "attributes"

    def _switch_to_layout(self) -> None:
        self.current_view = "layout"

    def _build_back_menu(self, label: str) -> rio.Component:
        return rio.PointerEventListener(
            rio.Rectangle(
                content=rio.Row(
                    rio.Icon(
                        "material/arrow_back",
                        min_width=2.2,
                        min_height=2.2,
                    ),
                    rio.Text(
                        label,
                        selectable=False,
                        style="heading2",
                        justify="left",
                        grow_x=True,
                    ),
                    spacing=1,
                    margin=MARGIN,
                ),
                fill=rio.Color.TRANSPARENT,
                hover_fill=self.session.theme.neutral_palette.background_active,
                ripple=True,
                cursor="pointer",
                transition_time=0.1,
            ),
            on_press=self._switch_to_tree,
        )

    def _build_total_components(self) -> rio.Component:
        """
        Creates a component which displays the total number of components
        """
        n_total_components = len(self.session._weak_components_by_id)
        text = f"{n_total_components} components in total"

        if n_total_components <= 150:
            text += " (fast)"
            icon = "material/speed:fill"
            color = self.session.theme.success_color
        elif n_total_components <= 400:
            text += " (borderline)"
            icon = "material/warning:fill"
            color = self.session.theme.neutral_palette.foreground
        else:
            text += " (slow)"
            icon = "material/warning:fill"
            color = self.session.theme.warning_color

        # (The plural form "components" is safe here, since this page alone
        # has more than one component)
        return rio.Row(
            rio.Icon(
                icon=icon,
                fill=color,
            ),
            rio.Text(
                text,
                italic=True,
                fill=color,
            ),
            spacing=0.5,
            align_x=0.5,
        )

    def _build_tree_view(self) -> rio.Component:
        return rio.Column(
            rio.Row(
                rio.Text(
                    "Component Tree",
                    style="heading2",
                    justify="left",
                    grow_x=True,
                ),
                rio.Tooltip(
                    rio.debug.dev_tools.component_picker.ComponentPicker(),
                    "Select a component by clicking on it",
                ),
                margin_right=MARGIN,
            ),
            rio.debug.dev_tools.component_tree.ComponentTree(
                component_id=self.bind().selected_component_id,
                grow_y=True,
                # Note how there is no `margin_right` here. This is intentional
                # because the tree has an internal scroll bar which would look
                # silly if floating in space.
            ),
            # self._build_total_components(),
            rio.Button(
                "Attributes",
                icon="material/info",
                shape="rounded",
                on_press=self._switch_to_details,
                margin_right=MARGIN,
            ),
            rio.Button(
                "Layout",
                icon="material/space_dashboard",
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
        assert self.current_view == "attributes", self.current_view
        assert self.selected_component_id is not None

        # Get the target component
        try:
            target = self.session._weak_components_by_id[
                self.selected_component_id
            ]
            heading = type(target).__name__
        except KeyError:
            heading = "Attributes"

        # Delegate the hard work to another component
        return rio.Column(
            self._build_back_menu(heading),
            rio.ScrollContainer(
                component_attributes.ComponentAttributes(
                    component_id=self.bind().selected_component_id,
                    on_switch_to_layout_view=self._switch_to_layout,
                    margin_left=MARGIN,
                    margin_right=MARGIN,
                    margin_bottom=MARGIN,
                ),
                grow_y=True,
                scroll_x="never",
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
                    margin=MARGIN,
                ),
                grow_y=True,
                scroll_x="never",
            ),
        )

    def build(self) -> rio.Component:
        if self.current_view == "tree":
            return self._build_tree_view()

        if self.current_view == "attributes":
            return self._build_details_view()

        if self.current_view == "layout":
            return self._build_layout_view()

        raise AssertionError("Unreachable")
