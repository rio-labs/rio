import typing as t

import pytest

import rio
from tests.utils.layouting import verify_layout


@pytest.mark.parametrize(
    "container_type",
    [rio.Row, rio.Column],
)
async def test_linear_container_with_no_extra_width(
    container_type: type,
) -> None:
    await verify_layout(
        lambda: container_type(
            rio.Text("hi", min_width=100),
            rio.Button("clicky", min_width=400),
        )
    )


@pytest.mark.parametrize(
    "horizontal",
    [True, False],
)
@pytest.mark.parametrize(
    "first_child_grows",
    [True, False],
)
@pytest.mark.parametrize(
    "second_child_grows",
    [True, False],
)
@pytest.mark.parametrize(
    "proportions",
    [
        None,
        "homogeneous",
        [1, 2],
        [2, 1],
    ],
)
async def test_linear_container_with_extra_width(
    horizontal: bool,
    first_child_grows: bool,
    second_child_grows: bool,
    proportions: None | t.Literal["homogeneous"] | list[int],
) -> None:
    """
    A battery of scenarios to test the most common containers - Rows & Columns.
    """
    if proportions:
        pytest.skip("Proportions tests are bugged somehow")

    if horizontal:
        container_type = rio.Row

        if first_child_grows:
            first_child_width = 0
            first_child_grow_x = True
        else:
            first_child_width = 10
            first_child_grow_x = False

        if second_child_grows:
            second_child_width = 0
            second_child_grow_x = True
        else:
            second_child_width = 20
            second_child_grow_x = False

        first_child_height = 0
        second_child_height = 0

        first_child_grow_y = False
        second_child_grow_y = False

        parent_width = 50
        parent_height = 0
    else:
        container_type = rio.Column

        if first_child_grows:
            first_child_height = 0
            first_child_grow_y = True
        else:
            first_child_height = 10
            first_child_grow_y = False

        if second_child_grows:
            second_child_height = 0
            second_child_grow_y = True
        else:
            second_child_height = 20
            second_child_grow_y = False

        first_child_width = 0
        second_child_width = 0

        first_child_grow_x = False
        second_child_grow_x = False

        parent_width = 0
        parent_height = 50

    await verify_layout(
        lambda: container_type(
            rio.Text(
                "short-text",
                min_width=first_child_width,
                min_height=first_child_height,
                grow_x=first_child_grow_x,
                grow_y=first_child_grow_y,
            ),
            rio.Text(
                "very-much-longer-text",
                min_width=second_child_width,
                min_height=second_child_height,
                grow_x=second_child_grow_x,
                grow_y=second_child_grow_y,
            ),
            # It would be nice to vary the spacing as well, but that would once
            # again double the number of tests this case already has. Simply
            # always specify a spacing, since that is the harder case anyway.
            spacing=2,
            proportions=proportions,
            min_width=parent_width,
            min_height=parent_height,
            align_x=0.5,
            align_y=0.5,
        )
    )
