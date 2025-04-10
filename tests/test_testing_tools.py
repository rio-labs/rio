import rio.testing


async def test_active_page_url():
    url = "foo/bar"

    async with rio.testing.DummyClient(active_url=url) as test_client:
        assert test_client.session.active_page_url.path == "/" + url


async def test_crashed_build_functions_are_tracked():
    def build() -> rio.Component:
        return 3  # type: ignore

    async with rio.testing.DummyClient(build) as test_client:
        assert len(test_client.crashed_build_functions) == 1


async def test_rebuild_resets_crashed_build_functions():
    class CrashingComponent(rio.Component):
        fail: bool = True

        def build(self) -> rio.Component:
            if self.fail:
                raise RuntimeError
            else:
                return rio.Text("hi")

    async with rio.testing.DummyClient(CrashingComponent) as test_client:
        assert len(test_client.crashed_build_functions) == 1

        crashing_component = test_client.get_component(CrashingComponent)
        crashing_component.fail = False

        await test_client.wait_for_refresh()

        assert not test_client.crashed_build_functions
