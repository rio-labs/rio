import dataclasses

import rio.testing


async def test_fields_with_defaults():
    class TestComponent(rio.Component):
        foo: list[str] = dataclasses.field(init=False, default_factory=list)
        bar: int = dataclasses.field(init=False, default=5)

        def build(self) -> rio.Component:
            raise NotImplementedError()

    async with rio.testing.DummyClient(TestComponent) as test_client:
        component = test_client.get_component(TestComponent)
        assert component.foo == []
        assert component.bar == 5


async def test_post_init():
    class TestComponent(rio.Component):
        post_init_called: bool = False

        def __post_init__(self):
            self.post_init_called = True

        def build(self) -> rio.Component:
            return rio.Text("hi")

    async with rio.testing.DummyClient(TestComponent) as test_client:
        root_component = test_client.get_component(TestComponent)
        assert root_component.post_init_called
