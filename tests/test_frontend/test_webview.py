import asyncio

import rio
from rio.testing import BrowserClient


async def test_inner_html_script_auto_executes() -> None:
    """
    A `<script>` tag inside the innerHTML content must execute automatically
    and `rioSendMessage` must be available inside it. The message must
    reach the Python `on_message` handler.
    """
    messages: list[object] = []

    class TestComponent(rio.Component):
        def on_message(self, msg: object) -> None:
            messages.append(msg)

        def build(self) -> rio.Component:
            return rio.Webview(
                "<script>rioSendMessage('hello')</script>",
                on_message=self.on_message,
            )

    async with BrowserClient(TestComponent) as test_client:
        for _ in range(100):
            if messages:
                break
            await asyncio.sleep(0.1)

    assert messages == ["hello"]


async def test_inner_html_multiple_scripts() -> None:
    """
    If the HTML contains multiple `<script>` tags, `rioSendMessage` must
    be available in each of them.
    """
    messages: list[object] = []

    class TestComponent(rio.Component):
        def on_message(self, msg: object) -> None:
            messages.append(msg)

        def build(self) -> rio.Component:
            return rio.Webview(
                "<script>rioSendMessage('first')</script>"
                "<p>Hello</p>"
                "<script>rioSendMessage('second')</script>",
                on_message=self.on_message,
            )

    async with BrowserClient(TestComponent) as test_client:
        for _ in range(100):
            if len(messages) >= 2:
                break
            await asyncio.sleep(0.1)

    assert messages == ["first", "second"]


async def test_srcdoc_iframe_script_auto_executes() -> None:
    """
    A `<script>` tag inside a srcdoc iframe must execute automatically
    and `rioSendMessage` must be available inside it.
    """
    messages: list[object] = []

    class TestComponent(rio.Component):
        def on_message(self, msg: object) -> None:
            messages.append(msg)

        def build(self) -> rio.Component:
            return rio.Webview(
                "<html><body><script>rioSendMessage('from iframe')</script></body></html>",
                on_message=self.on_message,
            )

    async with BrowserClient(TestComponent) as test_client:
        for _ in range(100):
            if messages:
                break
            await asyncio.sleep(0.1)

    assert messages == ["from iframe"]


async def test_multiple_webviews_route_correctly() -> None:
    """
    Multiple Webview components on the same page must each route messages
    to their own Python `on_message` handler — for messages sent
    SYNCHRONOUSLY during script execution.

    Scope of this test (read carefully): Each inline `<script>` calls
    `rioSendMessage` immediately, while its own script is still executing.
    At that moment the injected binding still refers to that script's own
    Webview, so this passes even if the binding were a shared global. It
    therefore verifies the plumbing (script execution, binding injection,
    `webviewId` routing to the correct Python handler, and that coexisting
    scripts don't collide on declaration) — but it does NOT verify that
    `rioSendMessage` is scoped per Webview.

    What this test does NOT cover: messages sent ASYNCHRONOUSLY, i.e. from
    deferred callbacks such as `setTimeout`, event listeners or
    `IntersectionObserver`s, which run long after all scripts on the page
    have executed. That case is covered by
    `test_multiple_webviews_deferred_messages_route_correctly`, which fails
    if the binding leaks across Webviews. Do not "simplify" one of these
    tests away — they guard different properties.
    """
    messages_a: list[object] = []
    messages_b: list[object] = []

    class TestComponent(rio.Component):
        def on_message_a(self, msg: object) -> None:
            messages_a.append(msg)

        def on_message_b(self, msg: object) -> None:
            messages_b.append(msg)

        def build(self) -> rio.Component:
            return rio.Column(
                rio.Webview(
                    "<script>rioSendMessage('to A')</script>",
                    key="a",
                    on_message=self.on_message_a,
                ),
                rio.Webview(
                    "<script>rioSendMessage('to B')</script>",
                    key="b",
                    on_message=self.on_message_b,
                ),
            )

    async with BrowserClient(TestComponent) as test_client:
        for _ in range(100):
            if messages_a and messages_b:
                break
            await asyncio.sleep(0.1)

    assert messages_a == ["to A"], f"Expected ['to A'], got {messages_a}"
    assert messages_b == ["to B"], f"Expected ['to B'], got {messages_b}"


async def test_multiple_webviews_deferred_messages_route_correctly() -> None:
    """
    `rioSendMessage` must be scoped to its own Webview even when called
    asynchronously (e.g. from `setTimeout`, event listeners or
    `IntersectionObserver` callbacks), i.e. long after all inline scripts on
    the page have executed.
    """
    messages_a: list[object] = []
    messages_b: list[object] = []

    class TestComponent(rio.Component):
        def on_message_a(self, msg: object) -> None:
            messages_a.append(msg)

        def on_message_b(self, msg: object) -> None:
            messages_b.append(msg)

        def build(self) -> rio.Component:
            return rio.Column(
                rio.Webview(
                    "<script>setTimeout(() => rioSendMessage('deferred A'), 500)</script>",
                    key="a",
                    on_message=self.on_message_a,
                ),
                rio.Webview(
                    "<script>setTimeout(() => rioSendMessage('deferred B'), 500)</script>",
                    key="b",
                    on_message=self.on_message_b,
                ),
            )

    async with BrowserClient(TestComponent) as test_client:
        for _ in range(100):
            if messages_a and messages_b:
                break
            await asyncio.sleep(0.1)

    assert messages_a == ["deferred A"], (
        f"Expected ['deferred A'], got {messages_a}"
    )
    assert messages_b == ["deferred B"], (
        f"Expected ['deferred B'], got {messages_b}"
    )


async def test_use_strict_directive_is_preserved() -> None:
    """
    A leading `'use strict'` directive must keep working even though Rio wraps
    inline scripts in a block scope (where the directive would otherwise be a
    no-op). Rio detects the directive and repeats it at the top of the script.

    The directive may be preceded by whitespace and `//` / `/* */` comments.
    """
    messages: list[object] = []

    class TestComponent(rio.Component):
        def on_message(self, msg: object) -> None:
            messages.append(msg)

        def build(self) -> rio.Component:
            return rio.Webview(
                "<script>"
                "// leading comment\n"
                "/* and a block comment */\n"
                "'use strict';\n"
                "let mode = 'sloppy';\n"
                "try { undeclaredTestVariable = 1; }\n"
                "catch (e) { mode = 'strict'; }\n"
                "rioSendMessage(mode)"
                "</script>",
                on_message=self.on_message,
            )

    async with BrowserClient(TestComponent) as test_client:
        for _ in range(100):
            if messages:
                break
            await asyncio.sleep(0.1)

    assert messages == ["strict"], f"Expected ['strict'], got {messages}"


async def test_sloppy_mode_is_the_default() -> None:
    """
    Scripts without a `'use strict'` directive must keep running in sloppy
    mode. Rio must not strict-ify code that didn't ask for it.
    """
    messages: list[object] = []

    class TestComponent(rio.Component):
        def on_message(self, msg: object) -> None:
            messages.append(msg)

        def build(self) -> rio.Component:
            return rio.Webview(
                "<script>"
                "let mode = 'sloppy';\n"
                "try { anotherUndeclaredTestVariable = 1; }\n"
                "catch (e) { mode = 'strict'; }\n"
                "rioSendMessage(mode)"
                "</script>",
                on_message=self.on_message,
            )

    async with BrowserClient(TestComponent) as test_client:
        for _ in range(100):
            if messages:
                break
            await asyncio.sleep(0.1)

    assert messages == ["sloppy"], f"Expected ['sloppy'], got {messages}"


async def test_no_handler_does_not_crash() -> None:
    """
    When `on_message` is not set, calling `rioSendMessage` must not crash
    the component.
    """

    class TestComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Webview(
                "<script>rioSendMessage('hello')</script>",
            )

    async with BrowserClient(TestComponent) as test_client:
        await asyncio.sleep(1)
