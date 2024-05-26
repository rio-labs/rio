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
        # Spawn the dev tools if running in debug mode
        if self.session._app_server.debug_mode:
            # Avoid a circular import
            import rio.debug.dev_tools

            dev_tools = rio.debug.dev_tools.DevToolsSidebar()
        else:
            dev_tools = None

        # User content should automatically scroll if it grows too large, so we
        # wrap it in a ScrollContainer
        user_content = ScrollContainer(utils.safe_build(self.build_function))

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
