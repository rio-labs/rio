from utils import create_mockapp

import rio


async def test_default_values_arent_considered_explicitly_set():
    class SquareComponent(rio.Component):
        label: str

        def __init__(self, label: str, size: float = 5):
            super().__init__(width=size, height=size)

            self.label = label

        def build(self):
            return rio.Text(self.label, width=self.width, height=self.height)

    class RootComponent(rio.Component):
        text: str

        def build(self):
            square_component = SquareComponent(self.text, size=10)
            return rio.Container(square_component)

    async with create_mockapp(lambda: RootComponent("Hello")) as app:
        root_component = app.get_component(RootComponent)
        square_component = app.get_component(SquareComponent)

        # Create a new SquareComponent with the default size. Since we aren't
        # explicitly passing a size to the constructor, reconciliation should
        # keep the old size.
        root_component.text = "World"
        await root_component.force_refresh()

        assert square_component.label == "World"
        assert square_component.width == 10
        assert square_component.height == 10


async def test_reconcile_same_component_instance():
    def build():
        return rio.Container(rio.Text("Hello"))

    async with create_mockapp(build) as app:
        app.outgoing_messages.clear()

        root_component = app.get_component(rio.Container)
        await root_component.force_refresh()

        # Nothing changed, so there's no need to send any data to JS. But in
        # order to know that nothing changed, the framework would have to track
        # every individual attribute of every component. Since we forced the
        # root_component to refresh, it's reasonable to send that component's data to
        # JS.
        assert not app.outgoing_messages or app.last_updated_components == {
            root_component
        }


async def test_reconcile_not_dirty_high_level_component():
    # Situation:
    # HighLevelComponent1 contains HighLevelComponent2
    # HighLevelComponent2 contains LowLevelContainer
    # HighLevelComponent1 is rebuilt and changes the child of LowLevelContainer
    # -> LowLevelContainer is reconciled and dirty (because it has new children)
    # -> HighLevelComponent2 is reconciled but *not* dirty because its child was
    # reconciled
    # The end result is that there is a new component (the child of
    # LowLevelContainer), whose builder (HighLevelComponent2) is not "dirty". Make
    # sure the new component is initialized correctly despite this.
    class HighLevelComponent1(rio.Component):
        switch: bool = False

        def build(self):
            if self.switch:
                child = rio.Switch()
            else:
                child = rio.Text("hi")

            return HighLevelComponent2(rio.Column(child))

    class HighLevelComponent2(rio.Component):
        content: rio.Component

        def build(self):
            return self.content

    async with create_mockapp(HighLevelComponent1) as app:
        root_component = app.get_component(HighLevelComponent1)
        root_component.switch = True
        await app.refresh()

        assert any(
            isinstance(component, rio.Switch)
            for component in app.last_updated_components
        )


async def test_reconcile_unusual_types():
    class Container(rio.Component):
        def build(self) -> rio.Component:
            return CustomComponent(
                integer=4,
                text="bar",
                tuple=(2.0, rio.Text("baz")),
                byte_array=bytearray(b"foo"),
            )

    class CustomComponent(rio.Component):
        integer: int
        text: str
        tuple: tuple[float, rio.Component]
        byte_array: bytearray

        def build(self):
            return rio.Text(self.text)

    async with create_mockapp(Container) as app:
        root_component = app.get_component(Container)

        # As long as this doesn't crash, it's fine
        await root_component.force_refresh()


async def test_reconcile_by_key():
    class Toggler(rio.Component):
        toggle: bool = False

        def build(self):
            if not self.toggle:
                return rio.Text("Hello", key="foo")
            else:
                return rio.Container(rio.Text("World", key="foo"))

    async with create_mockapp(Toggler) as app:
        root_component = app.get_component(Toggler)
        text = app.get_component(rio.Text)

        root_component.toggle = True
        await app.refresh()

        assert text.text == "World"


async def test_key_prevents_structural_match():
    class Toggler(rio.Component):
        toggle: bool = False

        def build(self):
            if not self.toggle:
                return rio.Text("Hello")
            else:
                return rio.Text("World", key="foo")

    async with create_mockapp(Toggler) as app:
        root_component = app.get_component(Toggler)
        text = app.get_component(rio.Text)

        root_component.toggle = True
        await app.refresh()

        assert text.text == "Hello"


async def test_key_interrupts_structure():
    class Toggler(rio.Component):
        key_: str = "abc"

        def build(self):
            return rio.Container(rio.Text(self.key_), key=self.key_)

    async with create_mockapp(Toggler) as app:
        root_component = app.get_component(Toggler)
        text = app.get_component(rio.Text)

        root_component.key_ = "123"
        await app.refresh()

        # The container's key changed, so even though the structure is the same,
        # the old Text component should be unchanged.
        assert text.text == "abc"


async def test_structural_matching_inside_keyed_component():
    class Toggler(rio.Component):
        toggle: bool = False

        def build(self):
            if not self.toggle:
                return rio.Row(rio.Container(rio.Text("A"), key="foo"))
            else:
                return rio.Row(
                    rio.Container(rio.Text("B")),
                    rio.Container(rio.Text("C"), key="foo"),
                )

    async with create_mockapp(Toggler) as app:
        root_component = app.get_component(Toggler)
        text = app.get_component(rio.Text)

        root_component.toggle = True
        await app.refresh()

        # The container with key "foo" has moved. Make sure the structure inside
        # of it was reconciled correctly.
        assert text.text == "C"


async def test_key_matching_inside_keyed_component():
    class Toggler(rio.Component):
        toggle: bool = False

        def build(self):
            if not self.toggle:
                return rio.Container(
                    rio.Row(
                        rio.Container(rio.Text("A"), key="container"),
                        key="row",
                    ),
                )
            else:
                return rio.Row(
                    rio.Text("B"),
                    rio.Container(rio.Text("C"), key="container"),
                    key="row",
                )

    async with create_mockapp(Toggler) as app:
        root_component = app.get_component(Toggler)
        text = app.get_component(rio.Text)

        root_component.toggle = True
        await app.refresh()

        # The container with key "foo" has moved. Make sure the structure inside
        # of it was reconciled correctly.
        assert text.text == "C"


async def test_same_key_on_different_component_type():
    class ComponentWithText(rio.Component):
        text: str

        def build(self) -> rio.Component:
            return rio.Text(self.text)

    class Toggler(rio.Component):
        toggle: bool = False

        def build(self):
            if not self.toggle:
                return rio.Text("Hello", key="foo")
            else:
                return ComponentWithText("World", key="foo")

    async with create_mockapp(Toggler) as app:
        root_component = app.get_component(Toggler)
        text = app.get_component(rio.Text)

        root_component.toggle = True
        await app.refresh()

        assert text.text == "Hello"


async def test_text_reconciliation():
    class RootComponent(rio.Component):
        text: str = "foo"

        def build(self) -> rio.Component:
            return rio.Text(self.text)

    async with create_mockapp(RootComponent) as app:
        root = app.get_component(RootComponent)
        text = app.get_component(rio.Text)

        root.text = "bar"
        await app.refresh()

        assert text.text == root.text


async def test_grid_reconciliation():
    class RootComponent(rio.Component):
        num_rows: int = 1

        def build(self) -> rio.Component:
            rows = [[rio.Text(f"Row {n}")] for n in range(self.num_rows)]
            return rio.Grid(*rows)

    async with create_mockapp(RootComponent) as app:
        root = app.get_component(RootComponent)
        grid = app.get_component(rio.Grid)

        root.num_rows += 1
        await app.refresh()

        assert {root, grid} < app.last_updated_components
        assert len(grid._children) == root.num_rows


async def test_margin_reconciliation():
    class RootComponent(rio.Component):
        switch: bool = True

        def build(self) -> rio.Component:
            if self.switch:
                return rio.Column(*[rio.Text("hi") for _ in range(7)])
            else:
                return rio.Column(
                    rio.Text("hi", margin_left=1),
                    rio.Text("hi", margin_right=1),
                    rio.Text("hi", margin_top=1),
                    rio.Text("hi", margin_bottom=1),
                    rio.Text("hi", margin_x=1),
                    rio.Text("hi", margin_y=1),
                    rio.Text("hi", margin=1),
                )

    async with create_mockapp(RootComponent) as app:
        root = app.get_component(RootComponent)
        texts = list(app.get_components(rio.Text))

        root.switch = False
        await app.refresh()

        assert texts[0].margin_left == 1
        assert texts[1].margin_right == 1
        assert texts[2].margin_top == 1
        assert texts[3].margin_bottom == 1

        assert texts[4].margin_x == 1
        assert texts[4].margin_left == texts[4].margin_right == None

        assert texts[5].margin_y == 1
        assert texts[5].margin_top == texts[5].margin_bottom == None

        assert texts[6].margin == 1
        assert (
            texts[6].margin_left
            == texts[6].margin_right
            == texts[6].margin_top
            == texts[6].margin_bottom
            == None
        )


async def test_reconcile_instance_with_itself():
    # There used to be a bug where, when a widget was reconciled with itself, it
    # was removed from `Session._dirty_components`. So any changes in that
    # widget weren't sent to the frontend.

    class Container(rio.Component):
        child: rio.Component

        def build(self) -> rio.Component:
            return self.child

    def build() -> rio.Component:
        return Container(rio.Text("foo"))

    async with create_mockapp(build, use_ordered_dirty_set=True) as app:
        container = app.get_component(Container)
        child = app.get_component(rio.Text)

        # Change the child's state and make its parent rebuild
        child.text = "bar"
        container.child = child

        # In order for the bug to occur, the parent has to be rebuilt before the
        # child
        assert list(app.session._dirty_components) == [child, container]
        await app.refresh()

        assert app.last_updated_components == {child, container}
