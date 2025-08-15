import typing as t

import pytest

import rio
from tests.utils.layouting import BrowserClient


# This is a multi-purpose test:
# 1. Make sure layouting works as expected regardless of whether the user
#    content is small or large.
# 2. Some browser addons insert HTML elements into the <body> or <html>. Make sure
#    that doesn't screw up the layout.
@pytest.mark.parametrize("layout", ["small", "tall", "wide", "large"])
@pytest.mark.parametrize("create_extra_element_in", [None, "body", "html"])
@pytest.mark.parametrize("debug_mode", [False, True])
async def test_3rd_party_elements_dont_affect_layout(
    debug_mode: bool,
    create_extra_element_in: t.Literal["html", "body"] | None,
    layout: t.Literal["small", "tall", "wide", "large"],
) -> None:
    def build():
        if layout in ("small", "tall"):
            text = "hi"
        else:
            text = "hello" * 100

        if layout in ("tall", "large"):
            text = "\n".join([text] * 100)

        return rio.Text(text)

    async with BrowserClient(build, debug_mode=debug_mode) as client:
        if create_extra_element_in is not None:
            await client.execute_js(
                f"""
                let newElement = document.createElement('div');
                let parentElement = document.querySelector('{create_extra_element_in}');
                parentElement.appendChild(newElement);
                """
            )

        (
            user_content_width,
            user_content_height,
        ) = await client.execute_js(
            f"""
            let userContentContainer =
            document.querySelector("{
                ".rio-user-root-container-outer" if debug_mode else "html"
            }");
            
            [
                userContentContainer.clientWidth / globalThis.pixelsPerRem,
                userContentContainer.clientHeight / globalThis.pixelsPerRem,
            ];
            """
        )

        assert user_content_height == pytest.approx(
            await client.get_window_height()
        )

        dev_tools_sidebar_width = await client.get_dev_tools_sidebar_width()
        assert user_content_width == pytest.approx(
            await client.get_window_width() - dev_tools_sidebar_width
        )
