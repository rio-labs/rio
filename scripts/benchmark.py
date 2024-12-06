import asyncio
import cProfile
import itertools
import pstats
import time
import typing as t

import rio

# Other options for profiling:
#
# https://github.com/jiffyclub/snakeviz
# https://github.com/nvdv/vprof
# https://vmprof.readthedocs.org/
# https://github.com/kwlzn/pytracing
# https://pypi.org/project/line-profiler


class ComplexComponent(rio.Component):
    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text("Complex component"),
            rio.Row(
                rio.Container(rio.Button("Button 1")),
                rio.Container(rio.Button("Button 2")),
                rio.Container(rio.Button("Button 3")),
            ),
            rio.Text("End of complex component"),
        )


class BenchmarkComponent(rio.Component):
    child_factory: t.Callable[[], rio.Component] = lambda: rio.Text(
        "Starting..."
    )

    def __post_init__(self):
        self.benchmark_start_time = time.monotonic()
        self._child_factory_iter = itertools.islice(
            itertools.cycle(
                [
                    lambda: ComplexComponent(),
                    lambda: ComplexComponent(),
                    lambda: ComplexComponent(),
                ]
            ),
            500,
        )

    def build(self) -> rio.Component:
        asyncio.create_task(self._change())

        elapsed_time = int(time.monotonic() - self.benchmark_start_time)
        return rio.Column(
            rio.Text("Benchmarking..."),
            rio.Text(f"Elapsed time: {elapsed_time} sec"),
            self.child_factory(),
        )

    async def _change(self) -> None:
        try:
            self.child_factory = next(self._child_factory_iter)
        except StopIteration:
            self.session.close()
        else:
            self.force_refresh()


def main():
    # app = rio.App(
    #     build=BenchmarkComponent,
    # )
    # app.run_in_window()
    import rio.cli

    rio.cli.run(release=True)


with cProfile.Profile() as profile:
    main()

    stats = pstats.Stats(profile)


stats.sort_stats(pstats.SortKey.CUMULATIVE)
stats.print_stats(r"[/\\]rio[/\\]")
