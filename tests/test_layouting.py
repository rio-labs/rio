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


@pytest.mark.parametrize(
    "build_functions",
    [
        func
        for name, func in globals().items()
        if name.startswith("layout_test_")
    ],
)
@pytest.mark.async_timeout(20)
async def test_layout(
    build_functions: Iterable[Callable[[], rio.Component]],
) -> None:
    """
    Runs all of the layout tests above, i.e. all functions starting with
    `layout_test_`.

    Each function can return any number of components to test.
    """
    for build in build_functions:
        await verify_layout(build)


def layout_test_single_component() -> Iterable[rio.Component]:
    """
    Just one component - this should fill the whole screen.
    """
    yield rio.Text("Hi")


def layout_test_row_with_no_extra_width() -> Iterable[rio.Component]:
    for component in (rio.Row, rio.Column):
        yield component(
            rio.Text("hi", width=100),
            rio.Button("clicky", width=400),
        )


def layout_test_row_with_extra_width_and_no_growers() -> (
    Iterable[rio.Component]
):
    for component in (rio.Row, rio.Column):
        yield component(
            rio.Text("hi", width=5),
            rio.Button("clicky", width=10),
            width=25,
        )


def layout_test_row_with_extra_width_and_one_grower() -> (
    Iterable[rio.Component]
):
    for component in (rio.Row, rio.Column):
        yield component(
            rio.Text("hi", width=5),
            rio.Button("clicky", width="grow"),
            width=20,
        )


def layout_test_stack() -> Iterable[rio.Component]:
    yield rio.Stack(
        rio.Text("Small", width=10, height=20),
        rio.Text("Large", width=30, height=40),
    )


def layout_test_scrolling_in_both_directions() -> Iterable[rio.Component]:
    yield rio.ScrollContainer(
        rio.Text("hi", width=30, height=30),
        width=20,
        height=20,
        align_x=0.5,
        align_y=0.5,
    )


def layout_test_scrolling_horizontally() -> Iterable[rio.Component]:
    yield rio.ScrollContainer(
        rio.Text("hi", width=30, height=30),
        width=20,
        height=20,
        align_x=0.5,
        align_y=0.5,
        scroll_y="never",
    )


def layout_test_scrolling_vertically() -> Iterable[rio.Component]:
    yield rio.ScrollContainer(
        rio.Text("hi", width=30, height=30),
        width=20,
        height=20,
        align_x=0.5,
        align_y=0.5,
        scroll_x="never",
    )


def layout_test_ellipsized_text() -> Iterable[rio.Component]:
    yield rio.Text(
        "My natural size should become 0",
        wrap="ellipsize",
        align_x=0,
    )


def layout_test_flow_container(justify: str) -> Iterable[rio.Component]:
    for justify in ["left", "right", "center", "justified", "grow"]:
        yield rio.FlowContainer(
            rio.Text("foo", width=5),
            rio.Text("bar", width=10),
            rio.Text("qux", width=4),
            column_spacing=3,
            row_spacing=2,
            justify=justify,  # type: ignore
            width=20,
            align_x=0,
        )
