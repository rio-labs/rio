import asyncio
import inspect
import typing as t

import rio.testing


class TracingExtensionParent(rio.Extension):
    def __init__(self) -> None:
        # Keeps track of called functions
        self.function_call_log: list[str] = []

    def verify_and_clear_log(self, *expected: str) -> None:
        """
        Verifies that the recorded function calls match the expected ones. This
        disregards order!
        """

        assert set(self.function_call_log) == set(expected)
        self.function_call_log.clear()

    def _record_function_call(self) -> None:
        # Get the caller's name
        caller_name = inspect.stack()[1].function

        # Record it
        self.function_call_log.append(caller_name)

    # This function should be inherited and called
    @rio.extension_event.on_session_start
    def on_session_start_parent(
        self,
        event: rio.ExtensionSessionStartEvent,
    ) -> None:
        self._record_function_call()


class TracingExtensionChild(TracingExtensionParent):
    @rio.extension_event.on_app_start
    def on_app_start(
        self,
        event: rio.ExtensionAppStartEvent,
    ) -> None:
        self._record_function_call()

    @rio.extension_event.on_app_close
    def on_app_close(
        self,
        event: rio.ExtensionAppCloseEvent,
    ) -> None:
        self._record_function_call()

    # This function isn't registered at all and should not be called
    def on_session_start(
        self,
        event: rio.ExtensionSessionStartEvent,
    ) -> None:
        self._record_function_call()

    # This function is asynchronous, testing that the extension system awaits
    # functions as needed.
    @rio.extension_event.on_session_start
    def on_session_start_async(
        self,
        event: rio.ExtensionSessionStartEvent,
    ) -> None:
        self._record_function_call()

    @rio.extension_event.on_session_close
    def on_session_close(
        self,
        event: rio.ExtensionSessionCloseEvent,
    ) -> None:
        self._record_function_call()

    @rio.extension_event.on_page_change
    def on_page_change(
        self,
        event: rio.ExtensionPageChangeEvent,
    ) -> None:
        self._record_function_call()

    # This function is registered for multiple events and should be called for
    # each of them
    @rio.extension_event.on_session_start
    @rio.extension_event.on_session_close
    @rio.extension_event.on_page_change
    def on_multiple_events(
        self,
        event: t.Any,
    ) -> None:
        self._record_function_call()


async def test_extension_events() -> None:
    # Create an app
    app = rio.App(
        build=lambda: rio.Text("Hello"),
    )

    # Add an extension which records called events
    extension_instance = TracingExtensionChild()
    app._add_extension(extension_instance)

    assert len(extension_instance.function_call_log) == 0

    async with rio.testing.DummyClient(app) as test_client:
        # The test client doesn't support Rio's full feature set and so doesn't
        # actually call the app start/close events right now. Skip them

        # Expect: Session start events
        extension_instance.verify_and_clear_log(
            "on_session_start_async",
            "on_session_start_parent",
            "on_multiple_events",
        )

        # Navigate to another page
        test_client.session.navigate_to("/foobar")

        # Expect: Page change event
        #
        # Rio dispatches this event in an asyncio task. Give it some time to
        # run.
        await asyncio.sleep(0.1)

        extension_instance.verify_and_clear_log(
            "on_page_change",
            "on_multiple_events",
        )

    # Expect: Session close events
    extension_instance.verify_and_clear_log(
        "on_session_close",
        "on_multiple_events",
    )

    # The app close event is missing here for the same reason as above
