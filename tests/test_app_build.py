import rio.testing


async def test_fundamental_container_as_root():
    def build():
        return rio.Row(rio.Text("Hello"))

    async with rio.testing.TestClient(build) as test_client:
        row_component = test_client.get_component(rio.Row)
        text_component = test_client.get_component(rio.Text)

        assert {
            row_component,
            text_component,
        } <= test_client._last_updated_components
