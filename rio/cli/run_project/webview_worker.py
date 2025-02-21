import asyncio
import threading
import time
import typing as t

import rio

from . import run_models


class WebViewWorker:
    def __init__(
        self,
        *,
        push_event: t.Callable[[run_models.Event], None],
        debug_mode: bool,
        url: str,
    ) -> None:
        from ... import webview_shim

        self.push_event = push_event
        self.debug_mode = debug_mode
        self.url = url

        # If running, this is the webview window
        self.window: webview_shim.Window | None = None

    def run(self, initial_app: rio.App) -> None:
        """
        Starts the worker and blocks until the window is closed or
        `request_stop` is called. This function must be called from the main
        thread.
        """
        from ... import webview_shim

        assert self.window is None, "Already running"

        # Make sure this was called from the main thread.
        assert (
            threading.current_thread() is threading.main_thread()
        ), "Must be called from the main thread"

        # Fetch the icon
        icon_path = asyncio.run(initial_app._fetch_icon_as_png_path())

        # Create the window
        self.window = webview_shim.create_window(
            title=self._title_for_app(initial_app),
            url=self.url,
        )
        webview_shim.start_mainloop(icon=icon_path)

        # If we've reached this point, the window must have been closed.
        self.window = None

        # If the webview window is closed, tell the Arbiter about it.
        self.push_event(run_models.StopRequested())

    def request_stop(self) -> None:
        """
        Makes the worker stop soon after called. May be called multiple times,
        or even before startup has finished.
        """

        while self.window is not None:
            # Try to close the window
            try:
                self.window.destroy()

            # Closing can fail if the window hasn't entirely opened yet. In that
            # case try again in a bit.
            except KeyError:  # TODO: Why key error?
                time.sleep(0.05)  # TODO

            # Success. Make sure to forget the window.
            else:
                self.window = None

    def _title_for_app(self, app: rio.App) -> str:
        return app.name + (" (debug)" if self.debug_mode else "")

    def update_window_for_app(self, app: rio.App) -> None:
        if self.window is None:
            return

        self.window.set_title(self._title_for_app(app))
