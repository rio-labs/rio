# This silences the following error:
#
# Cancelling an overlapped future failed
# future: <_OverlappedFuture pending cb=[BaseProactorEventLoop._start_serving.<locals>.loop() at C:\Python312\Lib\asyncio\proactor_events.py:841, Task.task_wakeup()]>
# Traceback (most recent call last):
#   File "C:\Python312\Lib\asyncio\windows_events.py", line 71, in _cancel_overlapped
#     self._ov.cancel()
# OSError: [WinError 6] The handle is invalid

import asyncio.windows_events


def _cancel_overlapped(self):
    if self._ov is None:
        return

    try:
        self._ov.cancel()
    except OSError:
        pass

    self._ov = None


asyncio.windows_events._OverlappedFuture._cancel_overlapped = _cancel_overlapped  # type: ignore
