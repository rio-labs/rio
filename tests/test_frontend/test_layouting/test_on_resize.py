import rio
from tests.utils.layouting import verify_layout

recorded_events = []


class MyComponent(rio.Component):
    @rio.event.on_resize
    def handle_resize(self, width, height) -> None:
        global recorded_events
        print(f"Component resized to {width}x{height}")
        recorded_events.append((width, height))

    def build(self):
        return rio.Rectangle(
            fill=rio.Color.BLUE,
            min_width=5.0,
            min_height=10.0,
        )


async def test_size_observer_reports_content_dimensions():
    global recorded_events

    # Compute layout
    layout = await verify_layout(MyComponent)

    # Find components
    session = layout.session
    size_observer = next(
        c
        for c in session._weak_components_by_id.values()
        if isinstance(c, MyComponent)
    )
    rectangle = next(
        c
        for c in session._weak_components_by_id.values()
        if isinstance(c, rio.Rectangle)
    )

    observer_layout = layout._layouts_are[size_observer._id_]
    rectangle_layout = layout._layouts_are[rectangle._id_]

    print(f"Observer layout: {observer_layout}")
    print(f"Rectangle layout: {rectangle_layout}")

    # Verify layout dimensions
    observer_width = observer_layout.allocated_outer_width
    observer_height = observer_layout.allocated_outer_height
    rect_width = rectangle_layout.allocated_outer_width
    rect_height = rectangle_layout.allocated_outer_height

    assert observer_width == rect_width, (
        f"Widths do not match: observer={observer_width}, rectangle={rect_width}"
    )
    assert observer_height == rect_height, (
        f"Heights do not match: observer={observer_height}, rectangle={rect_height}"
    )

    print(
        f"Observer dimensions: {observer_width}x{observer_height},{session.pixels_per_font_height=}"
    )

    # Verify size event
    assert len(recorded_events) >= 1, "Expected at least one resize event"
    observed_width = recorded_events[-1][0]
    observed_height = recorded_events[-1][1]

    assert observed_width == observer_width, (
        f"Expected width {observer_width}, got {observed_width}"
    )
    assert observed_height == observer_height, (
        f"Expected height {observer_height}, got {observed_height}"
    )
