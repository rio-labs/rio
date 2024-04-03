from __future__ import annotations

from typing import *  # type: ignore

import rio

__all__ = [
    "currently_building_component",
]


# Before a component is built, this value is set to that component. This allows newly
# created components to infer their creator, as well as session.
#
# - `Component`: The component that is currently being built
# - `None`: The app's build method is currently being called
currently_building_component: rio.Component | None = None


# Same as `currently_building_component`, but holding that component's session.
#
# - `Session`: The session that owns the currently building component
# - `None`: No build is currently in progress
currently_building_session: rio.Session | None = None


# This counter is increased each time a component is built. It can thus be used to
# uniquely identify the build generation of every component.
build_generation: int = 0
