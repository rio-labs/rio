# The "zzz" in the file name is there to ensure that this file runs last, so
# that the remaining tests run without the monkeypatches applied.

import pytest
from utils import enable_component_instantiation

import rio.testing
from rio.debug.monkeypatches import apply_monkeypatches

apply_monkeypatches()


def test_components_cant_be_instantiated_outside_of_build_methods():
    with pytest.raises(Exception):
        rio.Row()


@enable_component_instantiation
def test_type_checking():
    rio.Text(
        "foo",
        key="key",
        wrap=True,
        margin_x=2,
        width="grow",
    )
    rio.Container(rio.Text("bar"))

    class Comp1(rio.Component):
        attr: list["int"]  # <- partially made of forward references

        def build(self) -> rio.Component:
            return rio.Text("")

    Comp1([1, 2, 3])


@pytest.mark.parametrize(
    "func",
    [
        lambda: rio.Text(b"foo"),  # type: ignore
    ],
)
@enable_component_instantiation
def test_type_checking_error(func):
    with pytest.raises(TypeError):
        func()


@pytest.mark.parametrize(
    "component_cls",
    [
        rio.Spacer,
        rio.Row,
        rio.Grid,
    ],
)
@enable_component_instantiation
def test_component_class_can_be_used_as_build_function(
    component_cls: type[rio.Component],
):
    _ = rio.PageView(fallback_build=component_cls)


async def test_init_cannot_read_state_properties():
    # Accessing state properties in `__init__` is not allowed because state
    # bindings aren't initialized yet at that point. In development mode, trying
    # to access a state property in `__init__` should raise an exception.
    init_executed = False
    accessing_foo_raised_exception = accessing_margin_top_raised_exception = (
        False
    )

    class IllegalComponent(rio.Component):
        foo: int

        def __init__(self, foo: int):
            super().__init__()

            self.foo = foo

            nonlocal accessing_foo_raised_exception
            try:
                _ = self.foo
            except Exception:
                accessing_foo_raised_exception = True

            nonlocal accessing_margin_top_raised_exception
            try:
                _ = self.margin_top
            except Exception:
                accessing_margin_top_raised_exception = True

            nonlocal init_executed
            init_executed = True

        def build(self) -> rio.Component:
            return rio.Text("hi", margin_top=self.margin_top)

    class Container(rio.Component):
        def build(self) -> rio.Component:
            return IllegalComponent(17)

    async with rio.testing.TestClient(Container):
        assert init_executed
        assert accessing_foo_raised_exception
        assert accessing_margin_top_raised_exception
