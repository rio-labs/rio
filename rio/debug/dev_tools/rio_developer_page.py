import cProfile
import io
import marshal
import typing as t
from pathlib import Path

import rio.debug.dev_tools.component_tree
import rio.debug.layouter

PROFILER: cProfile.Profile | None = None
CURRENTLY_PROFILING = False


class RioDeveloperPage(rio.Component):
    def _on_start_profiling(self) -> None:
        global PROFILER, CURRENTLY_PROFILING
        assert not CURRENTLY_PROFILING

        # Create a new profiler if one doesn't exist
        if PROFILER is None:
            PROFILER = cProfile.Profile()

        # Start profiling
        PROFILER.enable()
        CURRENTLY_PROFILING = True

        # Update the UI to reflect the change
        self.force_refresh()

    def _on_stop_profiling(self) -> None:
        global PROFILER, CURRENTLY_PROFILING
        assert PROFILER is not None
        assert CURRENTLY_PROFILING

        # Stop profiling
        PROFILER.disable()
        CURRENTLY_PROFILING = False

        # Update the UI to reflect the change
        self.force_refresh()

    async def _on_save_profile(self) -> None:
        assert PROFILER is not None

        # Get the profile as bytes
        buffer = io.BytesIO()
        PROFILER.create_stats()
        marshal.dump(PROFILER.stats, buffer)

        # Save them
        await self.session.save_file(
            file_contents=buffer.getvalue(),
            file_name="rio-profile.prof",
        )

    def _build_profiling_section(self) -> rio.Component:
        result = rio.Column(
            rio.Markdown(
                """
Records a profile using Python's built-in `cProfile` module. This can be useful
for identifying performance bottlenecks in your code.

1. Start profiling
1. Perform the actions you want to profile
1. Stop profiling
1. Save the profile to a file
1. Analyze the profile using tools such as `snakeviz`
"""
            ),
            spacing=0.5,
            margin=0.5,
        )

        # Start / Stop profiling
        if CURRENTLY_PROFILING:
            result.add(
                rio.Button(
                    "Pause Profiling",
                    icon="material/pause",
                    color="danger",
                    on_press=self._on_stop_profiling,
                )
            )
        else:
            result.add(
                rio.Button(
                    "Start Profiling"
                    if PROFILER is None
                    else "Continue Profiling",
                    icon="material/play_arrow",
                    style="major" if PROFILER is None else "minor",
                    on_press=self._on_start_profiling,
                )
            )

        # If a profile was already created, offer to save it
        if not CURRENTLY_PROFILING and PROFILER is not None:
            result.add(
                rio.Button(
                    "Save Profile",
                    icon="material/save",
                    on_press=self._on_save_profile,
                )
            )

        return result

    async def _on_dump_layout(self) -> None:
        def filter_function(component: rio.Component) -> bool:
            # Don't care about the connection lost popup
            if type(component).__name__ == "DefaultConnectionLostComponent":
                return False

            # Everything else is fine
            return True

        # Create the layouter
        ly = await rio.debug.layouter.Layouter.create(
            self.session,
            filter=filter_function,
        )

        # Dump
        out_dir = Path.cwd() / "rio-layout-dump"
        out_dir.mkdir(parents=True, exist_ok=True)

        def dump(which: t.Literal["should", "are"]) -> None:
            # Export the layouts to a JSON file
            ly.debug_dump_json(
                which=which,
                out=(out_dir / f"layout-{which}.json").open("w"),
            )

            # Export the layouts as image
            as_image = ly.debug_draw(which=which)
            as_image.save((out_dir / f"layout-{which}.png").open("wb"))

        ly.print_tree()

        dump("are")
        dump("should")

        print(f"Layout files have been dumped to `{out_dir.absolute()}`")

    def _build_layouting_section(self) -> rio.Component:
        return rio.Column(
            rio.Markdown(
                """
Exports information about what the layout should look like vs. what it actually
looks like.
                """
            ),
            rio.Button(
                "Dump Layout",
                icon="material/save",
                on_press=self._on_dump_layout,
            ),
            spacing=0.5,
            margin=0.5,
        )

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text(
                "Rio Developer",
                style="heading2",
                justify="left",
            ),
            rio.Revealer(
                header="Profiling",
                header_style="heading3",
                content=self._build_profiling_section(),
            ),
            rio.Revealer(
                header="Layouting",
                header_style="heading3",
                content=self._build_layouting_section(),
            ),
            spacing=1,
            margin=1,
            align_y=0,
        )
