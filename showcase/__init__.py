import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
from typing import *  # type: ignore

import rio
import rio.debug

theme = rio.Theme.from_color(
    # light=False,
)

CARD_STYLE = rio.BoxStyle(
    fill=theme.neutral_palette.background,
    corner_radius=theme.corner_radius_small,
    # shadow_color=theme.active_color.replace(opacity=0.1),
)

CARD_STYLE_HOVER = CARD_STYLE.replace(
    # fill=theme.surface_active_color,
)


@dataclass
class SomeData:
    a: int = 1
    b: str = "foo"
    c: list[int] = dataclasses.field(default_factory=list)
    foo_bar: bool = False


class KeyEventTester(rio.Component):
    event: rio.KeyDownEvent = rio.KeyDownEvent("unknown", "unknown", "", frozenset())

    def on_key_down(self, event: rio.KeyDownEvent) -> None:
        self.event = event

    def build(self) -> rio.Component:
        return rio.KeyEventListener(
            rio.Text(
                f"""Hardware key: {self.event.hardware_key}
Software key: {self.event.software_key}
Input text: {self.event.text}
Modifiers: {self.event.modifiers}""",
                multiline=True,
            ),
            on_key_down=self.on_key_down,
        )


class ExtendoItem(rio.Component):
    name: str

    def build(self) -> rio.Component:
        return rio.Row(
            rio.Icon("material/archive", width=1, height=1),
            rio.Text(
                f"Item Called: {self.name}",
                width="grow",
                align_x=1,
            ),
            width="grow",
        )


class ExtensibleList(rio.Component):
    child_names: list[str] = field(
        default_factory=lambda: ["Perma 1", "Perma 2"],
    )

    def on_extend(self) -> None:
        self.child_names = self.child_names + [f"New {len(self.child_names) + 1}"]

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Button("Extend", on_press=self.on_extend),
            rio.Column(
                *[ExtendoItem(name) for name in self.child_names],
                spacing=0.5,
            ),
        )


class Sidebar(rio.Component):
    search_text: str = ""
    expanded: bool = False
    popup_visible: bool = False
    text_buffer: str = "text-buffer-default"
    number_value: int | float = 1.234

    def _on_toggle_popup(self) -> None:
        self.popup_visible = not self.popup_visible

    def _on_slider_change(self, evt: rio.SliderChangeEvent) -> None:
        print(f"Slider has changed to {evt.value}")

    def build(self) -> rio.Component:
        return rio.Card(
            content=rio.ScrollContainer(
                rio.Column(
                    rio.Text(
                        "Rio UI",
                        style="heading1",
                        margin_top=1.0,
                    ),
                    rio.Text(
                        "The reactive UI library for Python",
                        style="heading2",
                        margin_top=0.6,
                    ),
                    rio.AutoForm(SomeData()),
                    rio.Grid(
                        [
                            rio.TextInput(
                                label="Plain",
                                text=Sidebar.search_text,
                                prefix_text="prefix",
                                on_change=lambda evt: print("plain-change:", evt.text),
                                is_sensitive=False,
                            ),
                            rio.TextInput(
                                label="Secret",
                                text=Sidebar.search_text,
                                is_secret=True,
                                suffix_text="suffix",
                                on_confirm=lambda evt: print(
                                    "secret-confirm:", evt.text
                                ),
                            ),
                        ],
                        [
                            rio.Button(
                                "Button",
                                # icon="bootstrap/zoom-out",
                                is_sensitive=bool(self.search_text),
                                color=(
                                    rio.Color.BLACK
                                    if bool(self.search_text)
                                    else rio.Color.RED
                                ),
                            ),
                            rio.ProgressCircle(
                                progress=None,
                            ),
                        ],
                    ),
                    rio.Dropdown(
                        {
                            "Foo": "bar",
                            "Baz": "spam",
                            "1": "1",
                            "2": "2",
                            "3": "3",
                            "4": "4",
                            "5": "5",
                            "6": "6",
                            "7": "7",
                            "8": "8",
                            "9": "9",
                            "10": "10",
                            "11": "11",
                            "12": "12",
                            "13": "13",
                            "14": "14",
                            "15": "15",
                            "16": "16",
                            "17": "17",
                            "18": "18",
                            "19": "19",
                            "20": "20",
                        },
                        label="Dropdown",
                        on_change=lambda ev: print(ev.value),
                    ),
                    ExtensibleList(),
                    KeyEventTester(),
                    rio.Row(
                        rio.Icon(
                            "archive",
                            fill=rio.Color.BLUE,
                            width=3.0,
                            height=3.0,
                        ),
                        rio.Icon(
                            "material/archive:fill",
                            fill=rio.LinearGradientFill(
                                (rio.Color.RED, 0),
                                (rio.Color.BLUE, 1),
                                angle_degrees=20,
                            ),
                            width=3.0,
                            height=3.0,
                        ),
                        rio.Icon(
                            "material/castle",
                            fill=rio.ImageFill(
                                Path(__file__).parent / "test.png",
                            ),
                            width=3.0,
                            height=3.0,
                        ),
                        align_x=0.5,
                        spacing=1,
                    ),
                    rio.Row(
                        rio.Text("⇇ Undef space ⇉"),
                    ),
                    rio.Slider(
                        on_change=self._on_slider_change,
                    ),
                    rio.Slider(
                        minimum=-5,
                        maximum=-2,
                        on_change=self._on_slider_change,
                    ),
                    rio.Slider(
                        minimum=-5,
                        maximum=2,
                        on_change=self._on_slider_change,
                    ),
                    rio.Slider(
                        minimum=2,
                        maximum=10,
                        step_size=2,
                        on_change=self._on_slider_change,
                    ),
                    rio.Button(
                        "Foo",
                        on_press=lambda: print("Button Pressed"),
                        shape="pill",
                        style="major",
                        is_loading=True,
                    ),
                    rio.Button(
                        "Bar",
                        icon="material/castle:fill",
                        shape="rounded",
                        style="minor",
                        color="danger",
                        # is_sensitive=False,
                    ),
                    rio.Button(
                        "Baz",
                        icon="material/archive:fill",
                        shape="rectangle",
                        color="warning",
                    ),
                    rio.Button(
                        "Spam",
                        color=rio.Color.CYAN,
                        width=3,
                        height=3,
                        align_x=0.5,
                    ),
                    rio.ProgressBar(0.4),
                    rio.ProgressBar(None),
                    rio.ColorPicker(
                        rio.Color.RED,
                        on_change=lambda evt: print("RGB Color Changed:", evt.color),
                    ),
                    rio.Drawer(
                        rio.Text("There's a colorpicker in here!"),
                        rio.ColorPicker(
                            rio.Color.GREEN,
                            pick_opacity=True,
                            on_change=lambda evt: print(
                                "RGBA Color Changed:", evt.color
                            ),
                            width=15,
                        ),
                        is_open=False,
                        side="right",
                        height=20,
                    ),
                    rio.Popup(
                        rio.Button(
                            "And a Popup!",
                            on_press=self._on_toggle_popup,
                        ),
                        rio.Text(
                            "Notice me!",
                            width=15,
                            height=10,
                        ),
                        is_open=Sidebar.popup_visible,
                        direction="top",
                        alignment=0.5,
                        gap=3.0,
                    ),
                    rio.Switch(
                        on_change=lambda _: print("Switch 1 Changed"),
                    ),
                    rio.Switch(
                        is_sensitive=False,
                        on_change=lambda _: print("Switch 2 Changed"),
                    ),
                    rio.NumberInput(
                        Sidebar.number_value,
                        label="Number",
                        prefix_text="$",
                        decimals=2,
                        on_change=lambda evt: print(
                            "Number Changed:", evt.value, self.number_value
                        ),
                    ),
                    rio.Text("I ❤️ U 🏎️"),
                    rio.Revealer(
                        "Revealer",
                        rio.Text("Hello World"),
                        on_change=lambda evt: print("Revealer Changed:", evt.is_open),
                        is_open=Sidebar.expanded,
                    ),
                    rio.ScrollTarget(
                        "scroll-target",
                        rio.Switch(
                            is_on=Sidebar.expanded,
                        ),
                    ),
                    rio.SwitcherBar(
                        names=[
                            "Home",
                            "Docs",
                            "Tools",
                            "About Us",
                        ],
                        icons=[
                            "home",
                            "book",
                            # "tools",
                            None,
                            "castle",
                        ],
                        values=[
                            "",
                            "documentation",
                            "tools",
                            "about",
                        ],
                        orientation="horizontal",
                        color="primary",
                    ),
                    rio.SwitcherBar(
                        names=[
                            "Home",
                            "Docs",
                            "Tools",
                            "About Us",
                        ],
                        icons=[
                            "home",
                            "book",
                            # "tools",
                            None,
                            "castle",
                        ],
                        values=[
                            "",
                            "documentation",
                            "tools",
                            "about",
                        ],
                        orientation="vertical",
                        color="primary",
                    ),
                    rio.Stack(
                        rio.Rectangle(
                            style=rio.BoxStyle(fill=rio.Color.RED),
                            ripple=True,
                            width=5,
                            height=5,
                            align_x=0,
                            align_y=0,
                        ),
                        rio.Rectangle(
                            style=rio.BoxStyle(fill=rio.Color.YELLOW),
                            ripple=True,
                            width=3,
                            height=7,
                            align_x=0,
                        ),
                        rio.Rectangle(
                            style=rio.BoxStyle(fill=rio.Color.GREEN),
                            ripple=True,
                            width=7,
                            height=3,
                            align_y=0,
                        ),
                    ),
                    rio.ListView(
                        rio.HeadingListItem("Heading 1", key="item1"),
                        rio.SimpleListItem("Simple 1", key="item2"),
                        rio.SimpleListItem("Simple 2", key="item3"),
                        rio.SimpleListItem("Simple 3", key="item4"),
                        rio.HeadingListItem("Heading 2", key="item5"),
                        rio.SimpleListItem("Simple 4", key="item6"),
                        rio.SimpleListItem("Simple 5", key="item7"),
                    ),
                    spacing=1.0,
                    align_y=0,
                ),
                scroll_x="never",
            ),
            margin=1.0,
        )


class Foo(rio.Component):
    text: str

    def build(self) -> rio.Component:
        return rio.Text(self.text)

    @rio.event.on_mount
    def _on_mount(self):
        print(f"Mounted: {self.text}")

    @rio.event.on_unmount
    def _on_unmount(self):
        print(f"Unmounted: {self.text}")


class FooButton(rio.Component):
    value: int

    def on_press(self) -> None:
        self.value += 1

    def build(self) -> rio.Component:
        if self.value % 2 == 0:
            child = Foo(f"Value: {self.value}")
        else:
            child = rio.Text(f"Value: {self.value}")

        return rio.Column(
            rio.Button("Press Me", on_press=self.on_press),
            child,
        )


class ComponentShowcase(rio.Component):
    def build(self) -> rio.Component:
        return rio.Row(
            Sidebar(
                # width=30,
            ),
            # rio.ProgressBar(
            #     height=2,
            #     width="grow",
            # ),
            rio.Container(
                rio.Table(
                    {
                        "baz": [
                            "one",
                            "two",
                            "three",
                            "four",
                            "five",
                            "six",
                            "seven",
                            "eight",
                            "nine",
                        ],
                        "foo": [1, 2, 3, 4, 5, 6, 7, 8, 9],
                        "bar": ["a", "b", "c", "d", "e", "f", "g", "h", "i"],
                    },
                    align_x=0.5,
                    align_y=0.5,
                ),
                width="grow",
                height="grow",
            ),
        )

    # @rio.event.periodic(1)
    # def _on_periodic(self) -> None:
    #     print(f"Periodic! {self}")


def validator_factory(sess: rio.Session) -> rio.debug.Validator:
    return rio.debug.Validator(
        sess,
        dump_directory_path=rio.common.GENERATED_DIR,
    )


app = rio.App(
    name="Rio Showcase",
    build=ComponentShowcase,
    on_session_start=lambda sess: print("Session Started"),
    on_session_close=lambda sess: print("Session Ended"),
    theme=theme,
)


if __name__ == "__main__":
    app._run_as_web_server(
        host="127.0.0.1",
        port=8001,
        quiet=False,
        running_in_window=False,
        validator_factory=validator_factory,
        internal_on_app_start=None,
    )
else:
    fastapi_app = app._as_fastapi(
        debug_mode=True,
        running_in_window=False,
        validator_factory=validator_factory,
        internal_on_app_start=None,
    )
