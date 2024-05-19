import rio.testing


async def test_crashed_build_functions_are_tracked():
    def build() -> rio.Component:
        return 3  # type: ignore

    async with rio.testing.TestClient(build) as test_client:
        assert len(test_client.crashed_build_functions) == 1


async def test_rebuild_resets_crashed_build_functions():
    class CrashingComponent(rio.Component):
        fail: bool = True

        def build(self) -> rio.Component:
            if self.fail:
                raise RuntimeError
            else:
                return rio.Text("hi")

    async with rio.testing.TestClient(CrashingComponent) as test_client:
        assert len(test_client.crashed_build_functions) == 1

        crashing_component = test_client.get_component(CrashingComponent)
        crashing_component.fail = False

        await test_client.refresh()

        assert not test_client.crashed_build_functions
