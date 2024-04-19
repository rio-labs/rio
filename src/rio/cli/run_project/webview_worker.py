import threading
import time
from typing import *  # type: ignore

from . import run_models

try:
    import webview  # type: ignore
except ImportError:
    if TYPE_CHECKING:
        import webview  # type: ignore
    else:
        webview = None


class WebViewWorker:
    def __init__(
        self,
        *,
        push_event: Callable[[run_models.Event], None],
        debug_mode: bool,
        url: str,
    ) -> None:
        self.push_event = push_event
        self.debug_mode = debug_mode
        self.url = url

        # If running, this is the webview window
        self.window: Optional[webview.Window] = None

    def run(self) -> None:
        """
        Starts the worker and blocks until the window is closed or
        `request_stop` is called. This function must be called from the main
        thread.
        """
        assert webview is not None
        assert self.window is None, "Already running"

        # Make sure this was called from the main thread.
        assert (
            threading.current_thread() is threading.main_thread()
        ), "Must be called from the main thread"

        # Create the window
        self.window = webview.create_window(
            # TODO: Get the app's name, if possible
            "Rio (debug)" if self.debug_mode else "Rio",
            url=self.url,
        )
        webview.start()

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
