import io
from typing import *  # type: ignore

import rio.data_models


def _explain_allocated_space_before_alignment(
    session: rio.Session,
    component: rio.Component,
    layout: rio.data_models.ComponentLayout,
    axis: Literal["width", "height"],
) -> str:
    """
    Given a component and its layout, return a human readable explanation for
    why the component was allocated the space it was. This doesn't account for
    alignment, but strictly explains the space handed down by the parent.
    """
    if axis == "width":
        allocated_space = layout.allocated_width_before_alignment
    else:
        allocated_space = layout.allocated_height_before_alignment

    # Try to get a specialized explanation based on the parent component
    try:
        parent = session._weak_components_by_id[layout.parent_id]
    except KeyError:
        return f"The component was allocated a {axis} of {allocated_space:.1f} by its parent."

    # Prepare some commonly used values
    if axis == "width":
        parent_allocated_space = layout.parent_allocated_width
        parent_natural_size = layout.parent_natural_width
    else:
        parent_allocated_space = layout.parent_allocated_height
        parent_natural_size = layout.parent_natural_height

    parent_class_name = type(parent).__name__

    # Toplevel?
    if component is session._user_root_component:
        return f"This is the app's top-level component. As such, it was allocated the full {allocated_space:.1f} units of {axis} available in the window."

    # Single container?
    if type(parent) in (
        rio.Container,
        rio.Card,
        rio.Button,
        rio.Link,
    ):
        return f"Because {parent_class_name} components pass on all available space to their children, the component's {axis} is the full {allocated_space:.1f} units available in its parent."

    # Row & Column
    if isinstance(parent, rio.Row) or isinstance(parent, rio.Column):
        # Minor axis?
        if (
            isinstance(parent, rio.Row)
            and axis == "height"
            or isinstance(parent, rio.Column)
            and axis == "width"
        ):
            return f"The component is placed in a {parent_class_name}. Since all children of {parent_class_name} components receive the full {axis}, it has received the full {allocated_space:.1f} units available in its parent."

        # Major axis
        #
        # Only child
        if len(parent.children) == 1:
            return f"Because the component is the only child of its parent {parent_class_name}, it has received the full {allocated_space:.1f} units available in its parent."

        # No additional space
        if parent_allocated_space < parent_natural_size + 0.1:
            return f"The component is placed in a {parent_class_name}. Because that {parent_class_name} doesn't have any superfluous space available, the component was allocated the available {allocated_space:.1f} units of {axis}."

        # Gather information about growers
        width_growers = 0
        height_growers = 0
        for child in parent.children:
            width_growers += child.width == "grow"
            height_growers += child.height == "grow"

        if axis == "width":
            n_growers = width_growers
            is_grower = component.width == "grow"
        else:
            n_growers = height_growers
            is_grower = component.height == "grow"

        # No growers
        if n_growers == 0:
            return f"The component is placed in a {parent_class_name}. Because none of the {parent_class_name} component's children are set to grow, the {parent_class_name} has split the superfluous space evenly between all children. Thus, this component has received {allocated_space:.1f} units of {axis}."

        # There are growers, but this is not one of them
        if not is_grower:
            return f"The component is placed in a {parent_class_name}. Because the component is not set to grow, the superfluous space was given to other children. Thus, this component was left with its minimum {allocated_space:.1f} units of {axis}."

        # Multiple growers, including this one
        if n_growers > 1:
            return f'The component is placed in a {parent_class_name}. The superfluous space was split evenly between all children with a `{axis}="grow"` attribute. Thus, this component was allocated {allocated_space:.1f} units of {axis}.'

        # Only grower
        return f'The component is placed in a {parent_class_name}. Because it is the only child of the {parent_class_name} component with a `{axis}="grow"` attribute, it has received all of the superfluous space available in its parent. Thus, it was allocated {allocated_space:.1f} units of {axis}.'

    # No specialized explanation is available. Fall back to a generic default
    return f"The component was allocated a {axis} of {allocated_space:.1f} by its parent {parent_class_name}."


async def _explain_layout_in_axis(
    session: rio.Session,
    component: rio.Component,
    layout: rio.data_models.ComponentLayout,
    axis: Literal["width", "height"],
) -> str:
    """
    Given a component, come up with a human readable explanation for why it was
    allocated the space it was, in a single direction.
    """
    # Prepare some values based on axis
    if axis == "width":
        allocated_space = layout.allocated_width
        specified_size = component.width
        natural_size = layout.natural_width
        total_margin = (
            component._effective_margin_left + component._effective_margin_right
        )
        direction = "horizontal"
        start = "left"
        end = "right"

    else:
        allocated_space = layout.allocated_height
        specified_size = component.height
        natural_size = layout.natural_height
        total_margin = (
            component._effective_margin_top + component._effective_margin_bottom
        )
        direction = "vertical"
        start = "top"
        end = "bottom"

    # How much space did the parent hand down?
    result = io.StringIO()
    result.write(
        _explain_allocated_space_before_alignment(
            session, component, layout, axis
        )
    )
    result.write(" ")

    # Alignment
    if allocated_space < natural_size + total_margin + 0.1:
        result.write(f"This matches the {axis} needed by the component.")
    elif component.align_x is None:
        result.write("Because no alignment is set, it uses all of that space.")
    else:
        result.write(
            f"Due to the {direction} alignment of {component.align_x:1f}, it only takes up the minimum amount of space it needs. {component.align_x * 100:.0f}% of the leftover space is on the {start} of the component, the remainder on the {end}."
        )

    # Warn if the specified size is less than the natural one
    if (
        isinstance(specified_size, (int, float))
        and specified_size < natural_size
    ):
        result.write(
            f"\n\nThe explicitly set {axis} of {specified_size:.1f} has no effect, because it is less than the component's natural {axis} of {natural_size:.1f}. Components can never be smaller than their natural size."
        )

    # Done!
    return result.getvalue()


async def explain_layout(
    session: rio.Session,
    component: rio.Component,
) -> tuple[str, str]:
    """
    Given a component, come up with a human readable explanation for why it was
    allocated the space it was.

    The result is a tuple containing:

    - Explanation for the component's width
    - Explanation for the component's height
    """

    # Get client-side layout information
    (layout,) = await session._get_component_layouts([component._id])

    # Explain yourself!
    result = (
        await _explain_layout_in_axis(session, component, layout, "width"),
        await _explain_layout_in_axis(session, component, layout, "height"),
    )

    return result
