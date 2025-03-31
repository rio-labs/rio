import rio.testing


async def test_one_page_view() -> None:
    def build():
        return rio.Column(
            rio.Text("Welcome", style="heading1"),
            rio.PageView(),
        )

    app = rio.App(
        build=build,
        pages=[
            rio.ComponentPage(
                name="Home",
                url_segment="",
                build=rio.Spacer,
            ),
        ],
    )

    async with rio.testing.DummyClient(app) as test_client:
        # Make sure the Spacer (which is located on the home page) exists
        test_client.get_component(rio.Spacer)


async def test_nested_page_views() -> None:
    def build():
        return rio.Column(
            rio.Text("Welcome", style="heading1"),
            rio.PageView(),
        )

    app = rio.App(
        build=build,
        pages=[
            rio.ComponentPage(
                name="Home",
                url_segment="",
                build=rio.PageView,
                children=[
                    rio.ComponentPage(
                        name="Inner Home",
                        url_segment="",
                        build=rio.Spacer,
                    ),
                ],
            ),
        ],
    )

    async with rio.testing.DummyClient(app) as test_client:
        # Make sure the Spacer (which is located on the innermost page) exists
        test_client.get_component(rio.Spacer)
