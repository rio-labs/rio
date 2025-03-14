"""
NumberInputs are weird in some ways because they're a high level component with
a TextInput inside. They have been broken in the past, so now we do some sanity
checks.
"""

import rio.testing


async def test_auto_focus():
    def build() -> rio.Component:
        return rio.NumberInput(auto_focus=True)

    async with rio.testing.TestClient(build) as test_client:
        text_input = test_client.get_component(rio.TextInput)
        assert test_client._last_component_state_changes[text_input][
            "auto_focus"
        ]


async def test_value_change_from_python():
    class RootComponent(rio.Component):
        number: float = 1.5

        def build(self) -> rio.Component:
            return rio.NumberInput(self.number, decimals=2)

    async with rio.testing.TestClient(RootComponent) as test_client:
        root = test_client.get_component(RootComponent)
        text_input = test_client.get_component(rio.TextInput)

        root.number = 2.0
        await test_client.refresh()
        assert text_input.text == "2.00"


async def test_value_change_from_frontend():
    class RootComponent(rio.Component):
        number: float = 1.5

        def build(self) -> rio.Component:
            return rio.NumberInput(self.bind().number)

    async with rio.testing.TestClient(RootComponent) as test_client:
        root = test_client.get_component(RootComponent)
        text_input = test_client.get_component(rio.TextInput)

        await text_input._on_message_({"type": "confirm", "text": "1.23"})
        assert root.number == 1.23
