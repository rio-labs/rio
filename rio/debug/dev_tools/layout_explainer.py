from __future__ import annotations

import io
from typing import *  # type: ignore

import rio.data_models

# TODO: Specific explanations for
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


# These components make use of the `"grow"` value with `width`, `height` or
# both.
CONTAINERS_SUPPORTING_GROW: Iterable[type[rio.Component]] = {
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

    height_explanation: str
    width_explanation: str

    warnings: list[str]
    width_warnings: list[str]

    decrease_width: list[str]
    increase_width: list[str]

    decrease_height: list[str]
    increase_height: list[str]

    _layout: rio.data_models.ComponentLayout

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
        (self._layout,) = await session._get_component_layouts([component._id])

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
        axis: Literal["width", "height"],
        suggest_shrink: Callable[[str], None],
        suggest_grow: Callable[[str], None],
    ) -> str:
        """
        Given a component and its layout, return a human readable explanation
        for why the component was allocated the space it was. This doesn't
        account for alignment, but strictly explains the space handed down by
        the parent.
        """
        if axis == "width":
            allocated_space_before_alignment = (
                self._layout.allocated_width_before_alignment
            )
        else:
            allocated_space_before_alignment = (
                self._layout.allocated_height_before_alignment
            )

        target_class_name = type(self.component).__name__

        # Try to get a specialized explanation based on the parent self.component
        try:
            parent = self.session._weak_components_by_id[self._layout.parent_id]
        except KeyError:
            return f"The self.component was allocated a {axis} of {allocated_space_before_alignment:.1f} by its parent."

        # Prepare some commonly used values
        if axis == "width":
            parent_allocated_space = self._layout.parent_allocated_width
            parent_natural_size = self._layout.parent_natural_width
            specified_size = self.component.width
        else:
            parent_allocated_space = self._layout.parent_allocated_height
            parent_natural_size = self._layout.parent_natural_height
            specified_size = self.component.height

        parent_class_name = type(parent).__name__

        # Toplevel?
        if self.component is self.session._get_user_root_component():
            return f"This is the app's top-level component. As such, the {target_class_name} was allocated the full a {axis} of {allocated_space_before_alignment:.1f} available in the window."

        # Single container?
        if type(parent) in FULL_SIZE_SINGLE_CONTAINERS:
            return f"Because `{parent_class_name}` components pass on all available space to their children, the component's {axis} is the full {allocated_space_before_alignment:.1f} units available in its parent."

        # Overlay
        if isinstance(parent, rio.Overlay):
            return f"Children of `Overlay` components aren't part of the normal layouting process. Instead, they're allocated the entire {axis} of the window, and can position themselves freely inside it using alignment. Because of this, the {target_class_name} was allocated the entire {allocated_space_before_alignment:.1f} units available in the window."

        # Row & Column
        if isinstance(parent, rio.Row) or isinstance(parent, rio.Column):
            # Minor axis?
            if (
                isinstance(parent, rio.Row)
                and axis == "height"
                or isinstance(parent, rio.Column)
                and axis == "width"
            ):
                if specified_size == "grow":
                    self.warnings.append(
                        f'The component has `{axis}="grow"` set, but it is placed inside of a `{parent_class_name}`. Because {parent_class_name}s pass on the entire available space in this direction to all children it has no effect.'
                    )

                return f"The component is placed inside of a {parent_class_name}. Since all children of {parent_class_name}s receive the full {axis}, it has received the entire {allocated_space_before_alignment:.1f} units available in its parent."

            # Major axis
            if parent.proportions is not None:
                suggest_shrink(
                    f"Adjust the `proportions` attribute of the parent to give less space to this {target_class_name}"
                )
                suggest_grow(
                    f"Adjust the `proportions` attribute of the parent to give more space to this {target_class_name}"
                )
                return f"The component is placed inside of a {parent_class_name}. Since the {parent_class_name} has a `proportions` attribute set, the available space was split up according to the proportions. Thus, this component was allocated a {axis} of {allocated_space_before_alignment:.1f}."

            # Only child
            if len(parent.children) == 1:
                return f"Because the component is the only child of its parent {parent_class_name}, it has received the full {allocated_space_before_alignment:.1f} units available in its parent."

            # No additional space
            if parent_allocated_space < parent_natural_size + 0.1:
                return f"The component is placed inside of a {parent_class_name}. Because that {parent_class_name} doesn't have any superfluous space available, the component was allocated the available {axis} of {allocated_space_before_alignment:.1f}."

            # Gather information about growers
            width_growers = 0
            height_growers = 0
            for child in parent.children:
                width_growers += child.width == "grow"
                height_growers += child.height == "grow"

            if axis == "width":
                n_growers = width_growers
                is_grower = self.component.width == "grow"
            else:
                n_growers = height_growers
                is_grower = self.component.height == "grow"

            shrink_by_growing_others = f'Assign `{axis}="grow"` to one of the other children of the `{parent_class_name}` component, so it takes up the superfluous space'
            grow_by_growing = f'Assign `{axis}="grow"` to the component, so it is preferentially assigned the superfluous space'
            grow_by_shrinking_others = f'Remove the `{axis}="grow"` from one of the other children of the `{parent_class_name}` component, so this component gets more of the superfluous space'

            # No growers
            if n_growers == 0:
                suggest_shrink(shrink_by_growing_others)
                suggest_grow(grow_by_growing)
                return f"The component is placed inside of a {parent_class_name}. Because none of the {parent_class_name}'s children are set to grow, the {parent_class_name} has split up the superfluous space evenly between all children. Thus, this component has received a {axis} of {allocated_space_before_alignment:.1f}."

            # There are growers, but this is not one of them
            if not is_grower:
                suggest_grow(grow_by_growing)
                return f"The component is placed inside of a {parent_class_name}. Because the component is not set to grow, the superfluous space was given to other children. Thus, this component was left with its minimum {axis} of {allocated_space_before_alignment:.1f}."

            # Multiple growers, including this one
            if n_growers > 1:
                suggest_shrink(shrink_by_growing_others)
                suggest_grow(grow_by_shrinking_others)
                return f'The component is placed inside of a {parent_class_name}. The superfluous space was split up evenly between all children with a `{axis}="grow"` attribute. Thus, this component was allocated a {axis} of {allocated_space_before_alignment:.1f}.'

            # Only grower
            suggest_shrink(shrink_by_growing_others)
            return f'The component is placed inside of a {parent_class_name}. Because it is the only child of the {parent_class_name} with a `{axis}="grow"` attribute, it has received all of the superfluous space available in its parent. Thus, it was allocated a {axis} of {allocated_space_before_alignment:.1f}.'

        # No specialized explanation is available. Fall back to a generic default
        return f"The component was allocated a {axis} of {allocated_space_before_alignment:.1f} by its parent {parent_class_name}."

    async def _explain_layout_in_axis(
        self,
        axis: Literal["width", "height"],
        suggest_shrink: Callable[[str], None],
        suggest_grow: Callable[[str], None],
    ) -> str:
        """
        Given a component, come up with a human readable explanation for why it was
        allocated the space it was, in a single direction.
        """
        # Prepare some values based on axis
        try:
            parent = self.session._weak_components_by_id[self._layout.parent_id]
        except KeyError:
            parent = None

        if axis == "width":
            allocated_space = self._layout.allocated_width
            allocated_space_before_alignment = (
                self._layout.allocated_width_before_alignment
            )
            specified_size = self.component.width
            natural_size = self._layout.natural_width
            total_margin = (
                self.component._effective_margin_left
                + self.component._effective_margin_right
            )
            x_or_y = "x"
            start = "left"
            end = "right"
            alignment = self.component.align_x
        else:
            allocated_space = self._layout.allocated_height
            allocated_space_before_alignment = (
                self._layout.allocated_height_before_alignment
            )
            specified_size = self.component.height
            natural_size = self._layout.natural_height
            total_margin = (
                self.component._effective_margin_top
                + self.component._effective_margin_bottom
            )
            x_or_y = "y"
            start = "top"
            end = "bottom"
            alignment = self.component.align_y

        target_class_name = type(self.component).__name__

        # Warn if the component has a `grow` attribute set, but is placed inside
        # of a container that doesn't support it
        if (
            specified_size == "grow"
            and parent is not None
            and type(parent) not in CONTAINERS_SUPPORTING_GROW
        ):
            self.warnings.append(
                f'The component has `{axis}="grow"` set, but it is placed inside of a `{type(parent).__name__}`. {type(parent).__name__} components can not make use of this property, so it has no effect.'
            )

        # How much space did the parent hand down?
        result = io.StringIO()
        result.write(
            self._explain_allocated_space_before_alignment(
                axis,
                suggest_shrink=suggest_shrink,
                suggest_grow=suggest_grow,
            )
        )
        result.write(" ")

        # Alignment
        if allocated_space_before_alignment < natural_size + total_margin + 0.1:
            result.write(f"This matches the {axis} needed by the component.")
        elif alignment is None:
            result.write(
                "Because no alignment is set, it uses all of that space."
            )
        else:
            result.write("\n\n")
            result.write(
                f"Due to `align_{x_or_y}` having been given, the {target_class_name} only takes up the minimum amount of space necessary"
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

        # Warn if the specified size is less than the natural one
        if (
            isinstance(specified_size, (int, float))
            and specified_size < natural_size
        ):
            self.warnings.append(
                f"\n\nThe explicitly set {axis} of {specified_size:.1f} has no effect, because it is less than the component's natural {axis} of {natural_size:.1f}. Components can never be smaller than their natural size."
            )

        # Suggest growing the component by setting an explicit size
        if allocated_space == 0:
            suggest_grow(f"Assign a `{axis}` to the component")
        else:
            suggest_grow(
                f"Assign a `{axis}` to the component that is greater than its allocated {axis} of {allocated_space:.1f}"
            )

        # If the component has more space available than it needs, suggest using
        # an alignment to shrink
        if allocated_space > natural_size + 0.1:
            suggest_shrink(
                f"Align the component using `align_{x_or_y}`, so it only takes up its natural {axis}"
            )

        # If the component isn't aligned, suggest to grow it by growing its
        # parent
        if alignment is None:
            suggest_grow(
                f"Increase the {axis} of the parent component, so it hands down more space to the {target_class_name}"
            )

        # Done!
        return result.getvalue()
