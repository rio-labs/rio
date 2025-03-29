__all__ = [
    "active_window",
    "create_window",
    "OPEN_DIALOG",
    "SAVE_DIALOG",
    "start",
    "util",
    "errors",
    "Window",
]

import os

# There is an issue with `rye test`. rye passes a `--rootdir` argument to
# pytest, and webview parses command line arguments when it is imported. It
# crashes parsing the `--rootdir` argument, so we'll temporarily remove the
# command line arguments while importing webview.
import sys
import typing as t
from pathlib import Path

argv = sys.argv
sys.argv = argv[:1]


try:
    # `pywebview` supports a number of backends, each with its own pros and
    # cons. QT seems to be the best option for us: It runs on all platforms,
    # supports most if not all features (like setting the window icon) and is
    # likely to remain actively maintained.
    #
    # Just importing `webview` doesn't do the trick though. It uses `qtpy`,
    # which in turn supports multiple backends. We specifically want it to use
    # `PySide6` as that one comes with the most powerful, chromium-powered web
    # engine. By importing `PySide6` before importing `webview`, we ensure that
    # `qtpy` will pick `PySide6` as the backend.
    #
    # There's some related discussion on GitHub:
    # https://github.com/rio-labs/rio/issues/164
    import PySide6 as PySide6  # type: ignore (optional dependency)
    import qtpy  # type: ignore (optional dependency)

    assert qtpy.PYSIDE6, "PySide6 must be the backend for webview"

    # Re-export the webview API, so this file can be used as though it were the
    # `webview` module.
    from webview import (
        OPEN_DIALOG,
        SAVE_DIALOG,
        Window,
        active_window,
        create_window,
        errors,
        start,
        util,
    )
finally:
    sys.argv = argv


def start_mainloop(
    func: t.Callable[[], None] | None = None,
    *,
    icon: Path | None = None,
) -> None:
    start(
        func,
        gui=t.cast(t.Any, os.environ.get("RIO_WEBVIEW_GUI", "qt")),
        debug=os.environ.get("RIO_WEBVIEW_DEBUG") == "1",
        icon=None if icon is None else str(icon),
    )
