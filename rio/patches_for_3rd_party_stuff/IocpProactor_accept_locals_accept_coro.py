# This module silences the following warning:
#
# Task exception was never retrieved
#
# future: <Task finished name='Task-58'
# coro=<IocpProactor.accept.<locals>.accept_coro() done, defined at
# C:\Python312\Lib\asyncio\windows_events.py:558> exception=OSError(22, 'The I/O
#   operation has been aborted because of either a thread exit or an application
#     request', None, 995, None)> Traceback (most recent call last): File
# "C:\Python312\Lib\asyncio\windows_events.py", line 561, in accept_coro await
# future OSError: [WinError 995] The I/O operation has been aborted because of
# either a thread exit or an application request

import asyncio.windows_events

import introspection


def query_task_exception(task: asyncio.Task) -> None:
    try:
        task.exception()
    except:
        pass


# Since the offending function (`accept_coro`) is a nested function, the only
# solution I can think of is to monkeypatch `tasks.ensure_future`
tasks_module = asyncio.windows_events.tasks  # type: ignore


class tasks:
    @staticmethod
    def ensure_future(*args, **kwargs):
        task = asyncio.ensure_future(*args, **kwargs)
        task.add_done_callback(query_task_exception)
        return task


def accept(original_method, *args, **kwargs):
    asyncio.windows_events.tasks = tasks  # type: ignore

    try:
        return original_method(*args, **kwargs)
    finally:
        asyncio.windows_events.tasks = tasks_module  # type: ignore


introspection.wrap_method(asyncio.windows_events.IocpProactor, accept)  # type: ignore
