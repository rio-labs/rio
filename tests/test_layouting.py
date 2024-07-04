from collections.abc import Callable
from typing import *  # type: ignore

import pytest

import rio.data_models
import rio.testing
from tests.utils.headless_client import HeadlessClient

pytestmark = pytest.mark.async_timeout(20)


async def verify_layout(build: Callable[[], rio.Component]) -> None:
    """
    Rio contains two layout implementations: One on the client side, which
    determines the real layout of components, and a second one on the server
    side which is used entirely for testing.

    This function verifies that the results from the two layouters are the same.
    """
    async with HeadlessClient(build) as test_client:
        layouter = await test_client.create_layouter()

        for component_id, layout_should in layouter._layouts_should.items():
            layout_is = layouter._layouts_are[component_id]

            differences = list[str]()
            for attribute in rio.data_models.ComponentLayout.__annotations__:
                # Not all attributes are meant to be compared
                if attribute == "parent_id":
                    continue

                value_should = getattr(layout_should, attribute)
                value_is = getattr(layout_is, attribute)

                difference = abs(value_is - value_should)
                if difference > 0.2:
                    differences.append(
                        f"{attribute}: {value_is} != {value_should}"
                    )

            if differences:
                component = test_client.get_component_by_id(component_id)
                raise ValueError(
                    f"Layout of component {component} is incorrect:\n- "
                    + "\n- ".join(differences)
                )


@pytest.mark.parametrize(
    "text",
    [
        "",
        "short-text",
        "-".join(["long-text"] * 100),
    ],
)
async def test_single_component(text: str) -> None:
    """
    Just one component - this should fill the whole screen.
    """
    await verify_layout(lambda: rio.Text(text))


@pytest.mark.parametrize(
    "container_type",
    [rio.Row, rio.Column],
)
async def test_linear_container_with_no_extra_width(
    container_type: Type,
) -> None:
    await verify_layout(
        lambda: container_type(
            rio.Text("hi", width=100),
            rio.Button("clicky", width=400),
        )
    )


@pytest.mark.parametrize(
    "container_type",
    [rio.Row, rio.Column],
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
async def test_linear_container_with_extra_width_and_no_growers(
    container_type: Type,
    first_child_grows: bool,
    second_child_grows: bool,
    proportions: None | Literal["homogeneous"] | List[int],
) -> None:
    await verify_layout(
        lambda: container_type(
            rio.Text(
                "hi",
                width="grow" if first_child_grows else 5,
            ),
            rio.Button(
                "clicky",
                width="grow" if second_child_grows else 10,
            ),
            proportions=proportions,
            width=25,
        )
    )


async def test_stack() -> None:
    await verify_layout(
        lambda: rio.Stack(
            rio.Text("Small", width=10, height=20),
            rio.Text("Large", width=30, height=40),
        )
    )


async def test_scrolling_in_both_directions() -> None:
    await verify_layout(
        lambda: rio.ScrollContainer(
            rio.Text("hi", width=30, height=30),
            width=20,
            height=20,
            align_x=0.5,
            align_y=0.5,
        )
    )


async def test_scrolling_horizontally() -> None:
    await verify_layout(
        lambda: rio.ScrollContainer(
            rio.Text("hi", width=30, height=30),
            width=20,
            height=20,
            align_x=0.5,
            align_y=0.5,
            scroll_y="never",
        )
    )


async def test_scrolling_vertically() -> None:
    await verify_layout(
        lambda: rio.ScrollContainer(
            rio.Text("hi", width=30, height=30),
            width=20,
            height=20,
            align_x=0.5,
            align_y=0.5,
            scroll_x="never",
        )
    )


async def test_ellipsized_text() -> None:
    await verify_layout(
        lambda: rio.Text(
            "My natural size should become 0",
            wrap="ellipsize",
            align_x=0,
        )
    )


@pytest.mark.parametrize(
    "justify",
    [
        "left",
        "right",
        "center",
        "justified",
        "grow",
    ],
)
async def test_flow_container_layout(justify: str) -> None:
    await verify_layout(
        lambda: rio.FlowContainer(
            rio.Text("foo", width=5),
            rio.Text("bar", width=10),
            rio.Text("qux", width=4),
            column_spacing=3,
            row_spacing=2,
            justify=justify,  # type: ignore
            width=20,
            align_x=0,
        )
    )
