import rio.testing
from rio.debug.layouter import Layouter


class ResizeEventRecorder(rio.Component):
    recorded_events: list[rio.ComponentResizeEvent] = []

    @rio.event.on_resize
    def on_resize(self, resize_event: rio.ComponentResizeEvent) -> None:
        self.recorded_events.append(resize_event)

    def build(self):
        return rio.Rectangle(
            fill=rio.Color.BLUE,
            min_width=5.0,
            min_height=10.0,
        )


async def test_size_observer_reports_content_dimensions():
    async with rio.testing.BrowserClient(ResizeEventRecorder) as client:
        resize_event_recorder = client.get_component(ResizeEventRecorder)
        rectangle = client.get_component(rio.Rectangle)

        layouter = await Layouter.create(client.session)
        recorder_layout = layouter.get_layout_is(resize_event_recorder)
        rectangle_layout = layouter.get_layout_is(rectangle)
        assert (
            recorder_layout.allocated_outer_width
            == rectangle_layout.allocated_outer_width
        )
        assert (
            recorder_layout.allocated_outer_height
            == rectangle_layout.allocated_outer_height
        )

        event = resize_event_recorder.recorded_events[-1]
        assert event.width == recorder_layout.allocated_outer_width
        assert event.height == recorder_layout.allocated_outer_height
