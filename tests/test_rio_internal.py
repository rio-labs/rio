import asyncio

import pytest

import rio.testing
from rio.debug.monkeypatches import apply_monkeypatches, unapply_monkeypatches


@pytest.fixture(scope="module", autouse=True)
def temporarily_enabled_monkeypatches():
    apply_monkeypatches()
    yield
    unapply_monkeypatches()


async def test_root_components():
    async with rio.testing.DummyClient(rio.Spacer) as client:
        high_level_root = client.session._high_level_root_component
        assert isinstance(
            high_level_root,
            rio.components.root_components.HighLevelRootComponent,
        ), high_level_root
        assert high_level_root._rio_internal_

        low_level_root = high_level_root._build_data_.build_result  # type: ignore
        assert isinstance(
            low_level_root,
            rio.components.root_components.FundamentalRootComponent,
        ), low_level_root
        assert low_level_root._rio_internal_


async def test_root_user_root_component():
    async with rio.testing.DummyClient(rio.Spacer) as client:
        user_root = client.get_component(rio.Spacer)
        assert not user_root._rio_internal_


async def test_component_page():
    app = rio.App(
        build=rio.PageView, pages=[rio.ComponentPage("test", "", rio.Spacer)]
    )

    async with rio.testing.DummyClient(app) as client:
        spacer = client.get_component(rio.Spacer)
        assert not spacer._rio_internal_


async def test_custom_dialog():
    class DialogOpener(rio.Component):
        @rio.event.on_mount
        async def open_dialog(self):
            await self.session.show_custom_dialog(rio.Spacer, style="custom")

        def build(self):
            return rio.Text("dummy")

    async with rio.testing.DummyClient(DialogOpener) as client:
        await asyncio.sleep(0.1)  # Wait for the dialog to open

        dialog_container = client.get_component(rio.DialogContainer)
        assert dialog_container._rio_internal_

        user_content = client.get_component(rio.Spacer)
        assert not user_content._rio_internal_


async def test_custom_dialog_with_extra_styling():
    class DialogOpener(rio.Component):
        @rio.event.on_mount
        async def open_dialog(self):
            await self.session.show_custom_dialog(rio.Spacer, style="default")

        def build(self):
            return rio.Text("dummy")

    async with rio.testing.DummyClient(DialogOpener) as client:
        await asyncio.sleep(0.1)  # Wait for the dialog to open

        dialog_container = client.get_component(rio.DialogContainer)
        assert dialog_container._rio_internal_

        context_switcher = client.get_component(rio.ThemeContextSwitcher)
        assert context_switcher._rio_internal_

        user_content = client.get_component(rio.Spacer)
        assert not user_content._rio_internal_


async def test_yes_no_dialog():
    class DialogOpener(rio.Component):
        @rio.event.on_mount
        async def open_dialog(self):
            await self.session.show_yes_no_dialog("ok?")

        def build(self):
            return rio.Text("dummy")

    async with rio.testing.DummyClient(DialogOpener) as client:
        await asyncio.sleep(0.1)  # Wait for the dialog to open

        dialog_container = client.get_component(rio.DialogContainer)
        assert dialog_container._rio_internal_

        button = client.get_component(rio.Button)
        assert button._rio_internal_


async def test_button():
    def build():
        return rio.Button("hi")

    async with rio.testing.DummyClient(build) as client:
        button = client.get_component(rio.components.button._ButtonInternal)
        assert button._rio_internal_


async def test_icon_button():
    def build():
        return rio.IconButton("material/castle")

    async with rio.testing.DummyClient(build) as client:
        button = client.get_component(
            rio.components.icon_button._IconButtonInternal
        )
        assert button._rio_internal_
