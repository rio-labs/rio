__all__ = [
    "active_window",
    "create_window",
    "start",
    "util",
    "errors",
    "Window",
    "FileDialog",
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
    # Re-export the webview API, so this file can be used as though it were the
    # `webview` module.
    from webview import (
        FileDialog,
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
    backend: t.Literal[
        "qt",
        "pyqt5",
        "pyside2",
        "pyqt6",
        "pyside6",
        "gtk",
        "cef",
        "mshtml",
        "edgechromium",
    ]
    | None = None,
) -> None:
    # `pywebview` supports a number of backends, each with its own pros and
    # cons. QT seems to be the best option for us: It runs on all platforms,
    # supports most if not all features (like setting the window icon) and is
    # likely to remain actively maintained.
    #
    # There's some related discussion on GitHub:
    # https://github.com/rio-labs/rio/issues/164
    if backend is None:
        backend = "pyside6"

    if backend in ("pyqt5", "pyside2", "pyqt6", "pyside6"):
        os.environ["QT_API"] = backend
        backend = "qt"

    start(
        func,
        gui=backend,
        debug=os.environ.get("RIO_WEBVIEW_DEBUG") == "1",
        icon=None if icon is None else str(icon),
    )
