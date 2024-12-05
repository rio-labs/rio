from __future__ import annotations

import typing as t

from .. import utils
from .component import Component
from .fundamental_component import FundamentalComponent

__all__ = ["HighLevelRootComponent", "FundamentalRootComponent"]


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

    `public`: False
    """

    build_function: t.Callable[[], Component]
    build_connection_lost_message_function: t.Callable[[], Component]

    def build(self) -> Component:
        # Spawn the dev tools if running in debug mode.
        if self.session._app_server.debug_mode:
            # Avoid a circular import
            import rio.debug.dev_tools

            dev_tools = rio.debug.dev_tools.DevToolsSidebar()
        else:
            dev_tools = None

        # Build the user's root component
        user_root = utils.safe_build(self.build_function)

        return FundamentalRootComponent(
            user_root,
            utils.safe_build(self.build_connection_lost_message_function),
            dev_tools=dev_tools,
        )


class FundamentalRootComponent(FundamentalComponent):
    """
    ## Metadata

    `public`: False
    """

    content: Component
    connection_lost_component: Component
    dev_tools: Component | None


FundamentalRootComponent._unique_id_ = "FundamentalRootComponent-builtin"
