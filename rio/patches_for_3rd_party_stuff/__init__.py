import sys

if sys.platform == "win32":
    from . import (
        IocpProactor_accept_locals_accept_coro,
        ProactorBasePipeTransport_call_connection_lost,
        _OverlappedFuture_cancel_overlapped,
    )

    del _OverlappedFuture_cancel_overlapped
    del IocpProactor_accept_locals_accept_coro
    del ProactorBasePipeTransport_call_connection_lost
