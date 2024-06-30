from collections.abc import Callable
from typing import *  # type: ignore

import pytest

import rio.data_models
import rio.testing
from tests.utils.headless_client import HeadlessClient


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


def layout_test_single_component() -> rio.Component:
    """
    Just one component - this should fill the whole screen.
    """
    return rio.Text("Hi")


def layout_test_row_with_no_extra_width() -> rio.Component:
    return rio.Row(
        rio.Text("hi", width=100),
        rio.Button("clicky", width=400),
    )


def layout_test_row_with_extra_width_and_no_growers() -> rio.Component:
    return rio.Row(
        rio.Text("hi", width=5),
        rio.Button("clicky", width=10),
        width=25,
    )


def layout_test_row_with_extra_width_and_one_grower() -> rio.Component:
    return rio.Row(
        rio.Text("hi", width=5),
        rio.Button("clicky", width="grow"),
        width=20,
    )


def layout_test_stack() -> rio.Component:
    return rio.Stack(
        rio.Text("Small", width=10, height=20),
        rio.Text("Large", width=30, height=40),
    )


def layout_test_scrolling_in_both_directions() -> rio.Component:
    return rio.ScrollContainer(
        rio.Text("hi", width=30, height=30),
        width=20,
        height=20,
        align_x=0.5,
        align_y=0.5,
    )


def layout_test_scrolling_horizontally() -> rio.Component:
    return rio.ScrollContainer(
        rio.Text("hi", width=30, height=30),
        width=20,
        height=20,
        align_x=0.5,
        align_y=0.5,
        scroll_y="never",
    )


def layout_test_scrolling_vertically() -> rio.Component:
    return rio.ScrollContainer(
        rio.Text("hi", width=30, height=30),
        width=20,
        height=20,
        align_x=0.5,
        align_y=0.5,
        scroll_x="never",
    )


def layout_test_ellipsized_text() -> rio.Component:
    return rio.Text(
        "My natural size should become 0",
        wrap="ellipsize",
        align_x=0,
    )


@pytest.mark.parametrize(
    "build",
    [
        build
        for name, build in globals().items()
        if name.startswith("layout_test_")
    ],
)
@pytest.mark.async_timeout(20)
async def test_layout(build: Callable[[], rio.Component]) -> None:
    await verify_layout(build)


@pytest.mark.parametrize(
    "justify",
    ["left", "right", "center", "justified", "grow"],
)
@pytest.mark.async_timeout(20)
async def test_flow_container_layout(justify: str) -> None:
    def build() -> rio.FlowContainer:
        return rio.FlowContainer(
            rio.Text("foo", width=5),
            rio.Text("bar", width=10),
            rio.Text("qux", width=4),
            column_spacing=3,
            row_spacing=2,
            justify=justify,  # type: ignore
            width=20,
            align_x=0,
        )

    await verify_layout(build)
