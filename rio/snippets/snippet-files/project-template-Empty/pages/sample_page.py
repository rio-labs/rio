import rio


# <component>
@rio.page(
    name="Sample Page",
    url_segment="",
)
class SamplePage(rio.Component):
    """
    This is an example Page. Pages are identical to other Components and only
    differ in how they're used.
    """

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text("My App", style="heading2"),
            rio.Text(
                "This is a sample page. Replace it with your own content."
            ),
            spacing=2,
            margin=2,
            align_x=0.5,
            align_y=0,
        )


# </component>
