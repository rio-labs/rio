# This module silences these annoying errors:
#
# ERROR:asyncio:Exception in callback _ProactorBasePipeTransport._call_connection_lost(None)
# handle: <Handle _ProactorBasePipeTransport._call_connection_lost(None)>
# Traceback (most recent call last):
#   File "C:\Python312\Lib\asyncio\events.py", line 84, in _run
#     self._context.run(self._callback, *self._args)
#   File "C:\Python312\Lib\asyncio\proactor_events.py", line 165, in _call_connection_lost
#     self._sock.shutdown(socket.SHUT_RDWR)
# ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host

from asyncio.proactor_events import _ProactorBasePipeTransport

import introspection


class SocketWrapper:
    def __init__(self, socket):
        self._socket = socket

    def shutdown(self, *args, **kwargs):
        # Sometimes it's a `PipeHandle` object instead of a socket for some
        # reason
        if not hasattr(self._socket, "shutdown"):
            return

        try:
            self._socket.shutdown(*args, **kwargs)
        except ConnectionResetError:
            pass

    def __getattr__(self, attr: str):
        return getattr(self._socket, attr)


def _call_connection_lost(
    wrapped_func, self: _ProactorBasePipeTransport, *args, **kwargs
):
    if not hasattr(self._sock, "shutdown"):  # type: ignore
        wrapped_func(self, *args, **kwargs)
        return

    self._sock = SocketWrapper(self._sock)  # type: ignore

    # Call the original method
    try:
        wrapped_func(self, *args, **kwargs)
    finally:
        # Clean up
        if self._sock is not None:  # type: ignore
            self._sock = self._sock._socket  # type: ignore


introspection.wrap_method(_ProactorBasePipeTransport, _call_connection_lost)
