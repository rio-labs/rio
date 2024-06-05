from __future__ import annotations

from collections.abc import Callable
from typing import *  # type: ignore

from .. import utils
from .component import Component
from .fundamental_component import FundamentalComponent
from .scroll_container import ScrollContainer

__all__ = ["HighLevelRootComponent"]


# The HighLevelRootComponent is the top-most element. It's a high-level element
# that is never re-built, which is convenient in many ways:
# 1. Every component except for the root component itself has a valid builder
# 2. The JS code is simpler because the root component can't have an
#    alignment or margin
# 3. Children of non-fundamental components are automatically initialized
#    correctly, so we don't need to duplicate that logic here
class HighLevelRootComponent(Component):
    """
    ## Metadata

    public: False
    """

    build_function: Callable[[], Component]
    build_connection_lost_message_function: Callable[[], Component]

    def build(self) -> Component:
        # Spawn the dev tools if running in debug mode.
        #
        # The browser handles scrolling automatically if the content grows too
        # large for the window, but when the dev tools are visible, they would
        # appear between the scroll bar and the scrolling content. To prevent
        # this, we'll wrap the user content in a ScrollContainer.
        #
        # Conditionally inserting this ScrollContainer would make a bunch of
        # code more messy, so we'll *always* insert the ScrollContainer but
        # conditionally disable it with `scroll='never'`.
        if self.session._app_server.debug_mode:
            # Avoid a circular import
            import rio.debug.dev_tools

            dev_tools = rio.debug.dev_tools.DevToolsSidebar()

            scroll = "auto"
        else:
            dev_tools = None
            scroll = "never"

        # Build the user's root component
        user_root = utils.safe_build(self.build_function)

        # Wrap it up in a scroll container, so the dev-tools don't scroll
        user_content = ScrollContainer(
            user_root,
            scroll_x=scroll,
            scroll_y=scroll,
        )

        return FundamentalRootComponent(
            user_content,
            utils.safe_build(self.build_connection_lost_message_function),
            dev_tools=dev_tools,
        )


class FundamentalRootComponent(FundamentalComponent):
    """
    ## Metadata

    public: False
    """

    content: Component
    connection_lost_component: Component
    dev_tools: Component | None


FundamentalRootComponent._unique_id = "FundamentalRootComponent-builtin"
