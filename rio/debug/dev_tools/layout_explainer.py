from __future__ import annotations

import io
import typing as t

import rio.data_models

# FIXME: Some explanations are nonsense, if an alignment is set. For example,
# setting grow to `True` does nothing if the component is aligned.

# FIXME: Specific explanations for
#
# - drawer
# - flow_container
# - grid
# - ListView
# - mouse_event_listener
# - popup
# - revealer
# - scroll_container
# - scroll_target


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


# These components make use of the `grow_...` attributes in at least one axis.
CONTAINERS_SUPPORTING_GROW: set[type[rio.Component]] = {
    rio.Column,
    rio.Grid,
    rio.Row,
}


class LayoutExplainer:
    """
    Given a component, comes up with human readable explanations for the
    assigned layout.
    """

    session: rio.Session
    component: rio.Component
    _parent: rio.Component | None

    height_explanation: str
    width_explanation: str

    warnings: list[str]
    width_warnings: list[str]

    decrease_width: list[str]
    increase_width: list[str]

    decrease_height: list[str]
    increase_height: list[str]

    _layout: rio.data_models.ComponentLayout
    _parent_layout: rio.data_models.ComponentLayout | None

    def __init__(self) -> None:
        raise ValueError(
            "Don't create this class directly. Instead use the `create_new` method"
        )

    @staticmethod
    async def create_new(
        session: rio.Session,
        component: rio.Component,
    ) -> LayoutExplainer:
        """
        Creates and populates a new `LayoutExplainer` instance.

        ## Raises

        `KeyError`: If the given component cannot be found client-side.
        """
        # Create the instance
        self = LayoutExplainer.__new__(LayoutExplainer)
        self.session = session
        self.component = component

        self.warnings = []

        self.decrease_width = []
        self.increase_width = []

        self.decrease_height = []
        self.increase_height = []

        # Fetch layout information. This is asynchronous
        (self._layout,) = await session._get_component_layouts([component._id_])

        if self._layout.parent_id is None:
            self._parent = None
            self._parent_layout = None
        else:
            self._parent = session._weak_components_by_id[
                self._layout.parent_id
            ]
            (self._parent_layout,) = await session._get_component_layouts(
                [self._layout.parent_id]
            )

        # Explain yourself!
        self.width_explanation = await self._explain_layout_in_axis(
            "width",
            suggest_shrink=self.decrease_width.append,
            suggest_grow=self.increase_width.append,
        )

        self.height_explanation = await self._explain_layout_in_axis(
            "height",
            suggest_shrink=self.decrease_height.append,
            suggest_grow=self.increase_height.append,
        )

        return self

    def _explain_allocated_space_before_alignment(
        self,
        axis_name: t.Literal["width", "height"],
        suggest_shrink: t.Callable[[str], None],
        suggest_grow: t.Callable[[str], None],
    ) -> str:
        """
        Given a component and its layout, return a human readable explanation
        for why the component was allocated the space it was. This doesn't
        account for alignment, but strictly explains the space handed down by
        the parent.
        """
        if axis_name == "width":
            allocated_space_before_alignment = (
                self._layout.allocated_outer_width
            )
            axis_xy = "x"
        else:
            allocated_space_before_alignment = (
                self._layout.allocated_outer_height
            )
            axis_xy = "y"

        target_class_name = type(self.component).__name__
        parent_class_name = type(self._parent).__name__

        # Try to get a specialized explanation based on the parent
        if self._parent_layout is None:
            return f"The component was allocated a {axis_name} of {allocated_space_before_alignment:.1f} by its parent."

        # Prepare some commonly used values
        if axis_name == "width":
            parent_allocated_size = self._parent_layout.allocated_inner_width
            parent_natural_size = self._parent_layout.natural_width
            is_grower = self.component.grow_x
        else:
            parent_allocated_size = self._parent_layout.allocated_inner_height
            parent_natural_size = self._parent_layout.natural_height
            is_grower = self.component.grow_y

        # Toplevel?
        if self.component is self.session._get_user_root_component():
            return f"This is the app's top-level component. As such, the {target_class_name} was allocated the full {axis_name} of {allocated_space_before_alignment:.1f} available in the window."

        # Single container?
        if type(self._parent) in FULL_SIZE_SINGLE_CONTAINERS:
            return f"Because `{parent_class_name}` components pass on all available space to their children, the component's {axis_name} is the full {allocated_space_before_alignment:.1f} units available in its parent."

        # Overlay
        if isinstance(self._parent, rio.Overlay):
            return f"Children of `Overlay` components aren't part of the normal layouting process. Instead, they're allocated the entire {axis_name} of the window, and can position themselves freely inside it using alignment. Because of this, the {target_class_name} was allocated the entire {allocated_space_before_alignment:.1f} units available in the window."

        # Dialog root elements
        if isinstance(self._parent, rio.DialogContainer):
            return f"Root components of dialogs are allocated the entire {axis_name} of the window, and can position themselves freely inside it using alignment. Because of this, the {target_class_name} was allocated the entire {allocated_space_before_alignment:.1f} units available in the window."

        # Row & Column
        if isinstance(self._parent, rio.Row) or isinstance(
            self._parent, rio.Column
        ):
            # Minor axis?
            if (
                isinstance(self._parent, rio.Row)
                and axis_name == "height"
                or isinstance(self._parent, rio.Column)
                and axis_name == "width"
            ):
                if is_grower:
                    self.warnings.append(
                        f"The component has `grow_{axis_xy}=True` set, but is placed inside of a `{parent_class_name}`. Because `{parent_class_name}`s pass on the entire available {axis_name} to all children it has no effect."
                    )

                return f"The component is placed inside of a `{parent_class_name}`. Since all children of `{parent_class_name}`s receive the full {axis_name}, it has received the entire {allocated_space_before_alignment:.1f} units available in its parent."

            # Major axis
            if self._parent.proportions is not None:
                suggest_shrink(
                    f"Adjust the `proportions` attribute of the parent to give less space to this {target_class_name}"
                )
                suggest_grow(
                    f"Adjust the `proportions` attribute of the parent to give more space to this {target_class_name}"
                )
                return f"The component is placed inside of a `{parent_class_name}`. Since the `{parent_class_name}` has a `proportions` attribute set, the available space was split up according to the proportions. Thus, this component was allocated a {axis_name} of {allocated_space_before_alignment:.1f}."

            # Only child
            if len(self._parent.children) == 1:
                return f"Because the component is the only child of its parent `{parent_class_name}`, it has received the full {allocated_space_before_alignment:.1f} units available in its parent."

            # No additional space
            if parent_allocated_size < parent_natural_size + 0.1:
                return f"The component is placed inside of a `{parent_class_name}`. Because that `{parent_class_name}` doesn't have any superfluous space available, the component was allocated the available {axis_name} of {allocated_space_before_alignment:.1f}."

            # Gather information about growers
            x_growers = 0
            y_growers = 0
            for child in self._parent.children:
                x_growers += child.grow_x
                y_growers += child.grow_y

            if axis_name == "width":
                n_growers = x_growers
                is_grower = self.component.grow_x
            else:
                n_growers = y_growers
                is_grower = self.component.grow_y

            shrink_by_growing_others = f"Assign `grow_{axis_xy}=True` to one of the other children of the `{parent_class_name}` component, so it takes up the superfluous space"
            grow_by_growing = f"Assign `grow_{axis_xy}=True` to the component, so it is preferentially assigned the superfluous space"
            grow_by_shrinking_others = f"Remove the `grow_{axis_xy}=True` from one of the other children of the `{parent_class_name}` component, so this component gets more of the superfluous space"

            # No growers
            if n_growers == 0:
                suggest_shrink(shrink_by_growing_others)
                suggest_grow(grow_by_growing)
                return f"The component is placed inside of a `{parent_class_name}`. Because none of the `{parent_class_name}`'s children are set to grow, the `{parent_class_name}` has split up the superfluous space evenly between all children. Thus, this component has received a {axis_name} of {allocated_space_before_alignment:.1f}."

            # There are growers, but this is not one of them
            if not is_grower:
                suggest_grow(grow_by_growing)
                return f"The component is placed inside of a `{parent_class_name}`. Because the component is not set to grow, the superfluous space was given to other children. Thus, this component was left with its minimum {axis_name} of {allocated_space_before_alignment:.1f}."

            # Multiple growers, including this one
            if n_growers > 1:
                suggest_shrink(shrink_by_growing_others)
                suggest_grow(grow_by_shrinking_others)
                return f"The component is placed inside of a `{parent_class_name}`. The superfluous space was split up evenly between all children with a `grow_{axis_xy}=True` attribute. Thus, this component was allocated a {axis_name} of {allocated_space_before_alignment:.1f}."

            # Only grower
            suggest_shrink(shrink_by_growing_others)
            return f"The component is placed inside of a `{parent_class_name}`. Because it is the only child of the `{parent_class_name}` with a `grow_{axis_xy}=True` attribute, it has received all of the superfluous space available in its parent. Thus, it was allocated a {axis_name} of {allocated_space_before_alignment:.1f}."

        # No specialized explanation is available. Fall back to a generic default
        return f"The component was allocated a {axis_name} of {allocated_space_before_alignment:.1f} by its parent `{parent_class_name}`."

    async def _explain_layout_in_axis(
        self,
        axis_name: t.Literal["width", "height"],
        suggest_shrink: t.Callable[[str], None],
        suggest_grow: t.Callable[[str], None],
    ) -> str:
        """
        Given a component, come up with a human readable explanation for why it was
        allocated the space it was, in a single direction.
        """
        # Prepare some values based on axis
        if axis_name == "width":
            allocated_size = self._layout.allocated_inner_width
            allocated_size_before_alignment = self._layout.allocated_outer_width
            specified_min_size = self.component.min_width
            natural_size = self._layout.natural_width
            total_margin = (
                self.component._effective_margin_left_
                + self.component._effective_margin_right_
            )
            axis_xy = "x"
            start = "left"
            end = "right"
            alignment = self.component.align_x
            is_grower = self.component.grow_x
        else:
            allocated_size = self._layout.allocated_inner_height
            allocated_size_before_alignment = (
                self._layout.allocated_outer_height
            )
            specified_min_size = self.component.min_height
            natural_size = self._layout.natural_height
            total_margin = (
                self.component._effective_margin_top_
                + self.component._effective_margin_bottom_
            )
            axis_xy = "y"
            start = "top"
            end = "bottom"
            alignment = self.component.align_y
            is_grower = self.component.grow_y

        target_class_name = type(self.component).__name__
        parent_class_name = type(self._parent).__name__

        # Warn if the component has a `grow` attribute set, but is placed inside
        # of a container that doesn't support it
        if (
            is_grower
            and self._parent is not None
            and type(self._parent) not in CONTAINERS_SUPPORTING_GROW
        ):
            self.warnings.append(
                f"The component has `grow_{axis_xy}=True` set, but is placed inside of a `{parent_class_name}`. {parent_class_name} components do not make use of this property, so it has no effect."
            )

        # Warn if the component is aligned, but has no natural size
        if alignment is not None and natural_size < 0.1:
            self.warnings.append(
                f"The component is aligned using `align_{axis_xy}` but it has no natural {axis_name}. Since aligned components receive the minimum amount of space necessary, and this component doesn't require any space, it will not be visible."
            )

        # How much space did the parent hand down?
        result = io.StringIO()
        result.write(
            self._explain_allocated_space_before_alignment(
                axis_name,
                suggest_shrink=suggest_shrink,
                suggest_grow=suggest_grow,
            )
        )
        result.write(" ")

        # Alignment
        if allocated_size_before_alignment < natural_size + total_margin + 0.1:
            result.write(
                f"This matches the {axis_name} needed by the component."
            )
        else:
            result.write(
                f"This is more than its natural {axis_name} of {natural_size:.1f}."
            )

            if alignment is None:
                result.write(
                    " Because no alignment is set, it uses all of that space."
                )
            else:
                result.write(
                    f"\n\nDue to `align_{axis_xy}` being set, the component only takes up the minimum amount of space necessary"
                )

                if alignment <= 0.03:
                    result.write(
                        f" and is located at the {start} of the available space."
                    )
                elif 0.47 <= alignment <= 0.53:
                    result.write(f" and is centered in the available space.")
                elif alignment >= 0.97:
                    result.write(
                        f" and is located at the {end} of the available space."
                    )
                else:
                    result.write(
                        f", with {alignment * 100:.0f}% of the leftover space on the {start}, and the remainder on the {end}."
                    )

        # If the component has multiple children, explain which child is
        # responsible for the component's size
        if (isinstance(self.component, rio.Row) and axis_name == "height") or (
            isinstance(self.component, rio.Column) and axis_name == "width"
        ):
            children = self.component.children
            if len(children) > 1:
                child_layouts = await self.session._get_component_layouts(
                    [child._id_ for child in children]
                )
                largest_child_index = max(
                    range(len(children)),
                    key=lambda index: getattr(
                        child_layouts[index], f"requested_outer_{axis_name}"
                    ),
                )
                largest_child = children[largest_child_index]
                largest_child_layout = child_layouts[largest_child_index]

                result.write(
                    f"\n\nThe largest child is the {number_to_rank(largest_child_index + 1)} one (a `{type(largest_child).__name__}`), with a {axis_name} of {getattr(largest_child_layout, f'requested_outer_{axis_name}'):,.1f}. This is what determined the component's natural {axis_name}."
                )

        # Warn if the specified minimum size is less than the natural one
        if 0 < specified_min_size < natural_size:
            self.warnings.append(
                f"The explicitly set minimum {axis_name} of {specified_min_size:.1f} has no effect, because it is less than the component's natural {axis_name} of {natural_size:.1f}. Components can never be smaller than their natural size."
            )

        # Suggest growing the component by setting an explicit size
        if allocated_size == 0:
            suggest_grow(f"Assign a `min_{axis_name}` to the component")
        else:
            suggest_grow(
                f"Assign a `min_{axis_name}` to the component that is greater than its allocated {axis_name} of {allocated_size:.1f}"
            )

        # If the component isn't aligned, suggest to grow it by growing its
        # parent
        if alignment is None:
            suggest_grow(
                f"Increase the {axis_name} of the parent component, so it hands down more space to the {target_class_name}"
            )

        # If the component has more space available than it needs, suggest
        # using an alignment to shrink
        if alignment is None and allocated_size > natural_size + 0.1:
            suggest_shrink(
                f"Align the component using `align_{axis_xy}`, so it only takes up its natural {axis_name}"
            )

        # If aligned and the minimum size exceeds the natural size, suggest
        # removing the minimum
        if alignment is not None and specified_min_size > natural_size:
            suggest_shrink(
                f"Remove the `min_{axis_name}` attribute from the component so it only takes up its natural {axis_name}"
            )

        # If aligned, the component can be grown by removing the alignment
        if (
            alignment is not None
            and (allocated_size + 0.1) < allocated_size_before_alignment
        ):
            suggest_grow(
                f"Remove the `align_{axis_xy}` attribute from the component, so it takes up all of the available space"
            )

        # If the component is at its minimum size, give tips on how to reduce
        # its minimum size further
        if allocated_size < natural_size + 0.1:
            for suggestion in self._explain_how_to_reduce_natural_size(
                axis_name
            ):
                suggest_shrink(suggestion)

        # Done!
        return result.getvalue()

    def _explain_how_to_reduce_natural_size(
        self, axis_name: t.Literal["width", "height"]
    ) -> t.Iterable[str]:
        if isinstance(self.component, rio.Text):
            if axis_name == "width":
                yield 'Set `overflow="wrap"` or `overflow="ellipsize"` to reduce the `Text`\'s natural width'


def number_to_rank(number: int) -> str:
    if number == 1:
        return "first"
    elif number == 2:
        return "second"
    elif number == 3:
        return "third"
    else:
        return f"{number}th"
