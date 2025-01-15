"""
A job scheduler / task scheduler extension for Rio. Python functions can be
scheduled to run periodically, with the scheduler taking care of catching
exceptions and rescheduling the job for the future.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import typing as t
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import rio

__all__ = [
    "JobScheduler",
]


T = t.TypeVar("T")
P = t.ParamSpec("P")


JobFunction: t.TypeAlias = t.Callable[
    [],
    datetime
    | None
    | timedelta
    | t.Literal["never"]
    | t.Awaitable[None | datetime | timedelta | t.Literal["never"]],
]


async def _call_sync_or_async_function(
    func: t.Callable[P, T | t.Awaitable[T]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    """
    Calls a function, which can be either synchronous or asynchronous and
    returns its result. All exceptions are propagated.
    """
    # Call the function
    result = func(*args, **kwargs)

    # If the result needs awaiting, do that
    if inspect.isawaitable(result):
        result = await result

    # Done
    return result  # type: ignore


@dataclass
class ScheduledJob:
    """
    A job that has been scheduled.
    """

    # The callback to run. Can be synchronous or asynchronous.
    callback: JobFunction

    # The interval at which this function is configured to run.
    interval: timedelta

    # A name for the job
    name: str

    # Whether the job should wait for the interval duration before running for
    # the first time
    wait_for_initial_interval: bool

    # Whether the job should be staggered to avoid a load spike at the app's
    # start
    soft_start: bool


class JobScheduler(rio.Extension):
    """
    An extension for scheduling recurring jobs with Rio.

    It's common for apps to have jobs that must be run at regular intervals.
    This extension provides a way to schedule such jobs, in a way that is both
    easy and guards against crashes.
    """

    def __init__(self) -> None:
        # Chain up
        super().__init__()

        # Stores all scheduled jobs
        self._jobs: t.List[ScheduledJob] = []

        # The asyncio jobs handling the scheduled jobs
        self._job_workers: t.List[asyncio.Task[None]] = []

        # Whether the app has already started
        self._is_running = False

    def schedule(
        self,
        job: JobFunction,
        interval: timedelta,
        *,
        name: str | None = None,
        wait_for_initial_interval: bool = True,
        soft_start: bool = True,
    ) -> JobScheduler:
        """
        Schedules a job to run periodically.

        Schedules `job` to be called every `interval`. This function takes
        care not to crash, even if the job fails. Exceptions are caught, logged
        and the job will be scheduled again in the future. Runs are not
        overlapping - the next run will only start after the previous one has
        finished, plus the configured interval.

        If `wait_for_initial_interval` is `True`, the job will wait for
        `interval` before being called for the first time. If `False`, it will
        be run immediately instead, and the interval only starts counting after
        that.

        When an app starts for the first time, many jobs can be scheduled to
        run simultaneously. This can lead to undue load spikes on the system. If
        `soft_start` is `True`, the jobs will be rolled out over time, with a
        few seconds of delay between each.

        The job may optionally return a result. If it returns a `datetime`,
        that time will be taken as the next time to run the job. If it returns
        a `timedelta` it will be used as the next interval (though subsequent
        runs will still use the default interval, unless they also return a
        `timedelta`). If it returns `"never"`, the job will be unscheduled and
        never runs again.

        Returns the scheduler object, for easy chaining.

        ## Parameters

        `job`: The function to run.

        `interval`: How often to run the job. If the job returns a time or
            timedelta, that will be used for the next run instead, before
            returning to this interval.

        `name`: An optional name for the job. This can help with debugging and
            deciphering logs.

        `wait_for_initial_interval`: Whether the job should wait for the
            interval duration before running for the first time. If `False`, it
            will run immediately instead, and the interval only starts counting
            after that.

        `soft_start`: Whether the job should be staggered to avoid a load spike
            at the app's start.

        ## Raises

        `ValueError`: If `interval` is less than or equal to zero.
        """
        # Get a name
        if name is None:
            name = f"Job #{len(self._jobs) + 1}"

        # Add the job to the list of all jobs
        job_object = ScheduledJob(
            callback=job,
            interval=interval,
            name=name,
            wait_for_initial_interval=wait_for_initial_interval,
            soft_start=soft_start,
        )
        self._jobs.append(job_object)

        # If the app has already started, queue the job
        if self._is_running:
            if job_object.wait_for_initial_interval:
                run_at = datetime.now(timezone.utc) + job.interval
            else:
                run_at = datetime.now(timezone.utc)

            self._job_workers.append(
                asyncio.create_task(self._job_worker(job_object, run_at))
            )

        # Return self for chaining
        return self

    @rio.extension_event.on_app_start
    async def _on_app_start(
        self,
        _: rio.extension_event.ExtensionAppStartEvent,
    ) -> None:
        """
        Schedule all jobs when the app starts.
        """
        assert (
            not self._is_running
        ), "Called on app start, but the extension is already running!?"
        self._is_running = True

        # Allow the code below to assume there's at least one job
        if not self._jobs:
            return

        # Come up with a game plan for when to start all jobs without causing
        # a load spike.
        #
        # All jobs that don't allow for a soft start are easy - run them now.
        soft_start_jobs: t.List[tuple[ScheduledJob, datetime]] = []
        now = datetime.now(timezone.utc)

        for job in self._jobs:
            # When does this job _want to_ run?
            if job.wait_for_initial_interval:
                run_at = now + job.interval
            else:
                run_at = now

            # Remember soft-start jobs for later
            if job.soft_start:
                soft_start_jobs.append((job, run_at))
                continue

            # Run other jobs ASAP
            self._job_workers.append(
                asyncio.create_task(self._job_worker(job, run_at))
            )

        # Sort the soft-start jobs by when they'll first run
        soft_start_jobs.sort(key=lambda x: x[1])

        # Start the first job immediately
        first_job, prev_job_start_time = soft_start_jobs[0]

        self._job_workers.append(
            asyncio.create_task(
                self._job_worker(first_job, prev_job_start_time),
            )
        )

        # Ensure a minimum spacing between the remainder
        for ii in range(1, len(soft_start_jobs)):
            cur_job, cur_job_start_time = soft_start_jobs[ii]

            cur_job_start_time = max(
                cur_job_start_time,
                prev_job_start_time + timedelta(seconds=10),
            )

            self._job_workers.append(
                asyncio.create_task(
                    self._job_worker(cur_job, cur_job_start_time),
                )
            )

        # Done
        assert len(self._job_workers) == len(self._jobs), (
            len(self._job_workers),
            len(self._jobs),
        )

    @rio.extension_event.on_app_close
    async def _on_app_close(
        self,
        _: rio.extension_event.ExtensionAppCloseEvent,
    ) -> None:
        """
        Shut down all jobs when the app closes.
        """
        # Cancel all jobs
        for job_worker in self._job_workers:
            job_worker.cancel()

        # Wait for them to finish
        await asyncio.gather(*self._job_workers, return_exceptions=True)

    async def _wait_until(
        self,
        point_in_time: datetime,
    ) -> None:
        """
        Does the obvious.
        """

        while True:
            # How long to wait?
            now = datetime.now(timezone.utc)
            wait_time = (point_in_time - now).total_seconds()

            # Done?
            if wait_time <= 0:
                break

            # Wait, but never for too long. This helps if the clock is changing,
            # the system doesn't handle sleeping well, or similar.
            wait_time = min(wait_time, 3600)
            await asyncio.sleep(wait_time)

    def _get_next_run_time(
        self,
        job: ScheduledJob,
        result: t.Any,
    ) -> datetime | t.Literal["never"]:
        """
        Given a job and the result of its last run, returns when it should run
        next.
        """
        now = datetime.now(timezone.utc)

        # If nothing was returned, stick to its regularly configured interval
        if result is None:
            return now + job.interval

        # If the job wants to run at a specific time, do that
        if isinstance(result, datetime):
            if result < now:
                logging.warning(
                    f'Job "{job.name}" has returned a time in the past. It will be run again ASAP.'
                )
                return result

        # If the job wants to run after a certain amount of time, accommodate
        # that
        if isinstance(result, timedelta):
            return now + result

        # Killjoy
        if result == "never":
            return "never"

        # Invalid result
        logging.warning(
            f'Job "{job.name}" has returned an invalid result. Rescheduling using its default interval.'
        )
        return now + job.interval

    async def _job_worker(
        self,
        job: ScheduledJob,
        next_run_at: datetime,
    ) -> None:
        """
        Wrapper that handles the safe running of a job.
        """

        while True:
            # Wait until it's time to run the job
            await self._wait_until(next_run_at)

            # Run it, taking care not to crash
            try:
                result = await _call_sync_or_async_function(job.callback)

            except asyncio.CancelledError:
                return

            except Exception:
                logging.exception(
                    f'Job "{job.name}" has crashed. Rescheduling.'
                )
                result = None

            # When should it run next?
            next_run_at_or_never = self._get_next_run_time(job, result)

            # Killjoy?
            if next_run_at_or_never == "never":
                return

            # Update the next run time
            next_run_at = next_run_at_or_never
