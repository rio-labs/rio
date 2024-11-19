__all__ = [
    "active_window",
    "create_window",
    "SAVE_DIALOG",
    "start",
    "util",
    "Window",
]

# There is an issue with `rye test`. rye passes a `--rootdir` argument to
# pytest, and webview parses command line arguments when it is imported. It
# crashes parsing the `--rootdir` argument, so we'll temporarily remove the
# command line arguments while importing webview.
import sys

argv = sys.argv
sys.argv = argv[:1]


try:
    # `pywebview` supports a number of backends, each with its own pros and cons. QT
    # seems to be the best option for us: It runs on all platforms, supports most if
    # not all features (like setting the window icon) and is likely to remain
    # actively maintained.
    #
    # Just importing `webview` doesn't do the trick though. It uses `qtpy`, which in
    # turn supports multiple backends. We specifically want it to use `PySide6` as
    # that one comes with the most powerful, chromium-powered web engine. By
    # importing `PySide6` before importing `webview`, we ensure that `qtpy` will
    # pick `PySide6` as the backend.
    #
    # There's some related discussion on GitHub:
    # https://github.com/rio-labs/rio/issues/164
    import PySide6 as PySide6
    import qtpy

    assert qtpy.PYSIDE6, "PySide6 must be the backend for webview"

    # Re-export the webview API, so this file can be used as though it were the
    # `webview` module.
    from webview import (
        SAVE_DIALOG,
        Window,
        active_window,
        create_window,
        start,
        util,
    )
finally:
    sys.argv = argv
