from __future__ import annotations

from pathlib import Path

import rio

# When launched via `rio run`, the usual ways to detect the "main file" (`import
# __main__` and `sys.argv`) don't work. So `rio run` explicitly tells us what
# the "main file" is by setting this variable.
rio_run_app_module_path: Path | None = None


# Before a component is built, this value is set to that component. This allows
# newly created components to determine their creator, as well as session.
#
# - `Component`: The component that is currently being built
# - `None`: The build method of the app itself is currently being called
currently_building_component: rio.Component | None = None


# Same as `currently_building_component`, but holding that component's session.
#
# - `Session`: The session that owns the currently building component
# - `None`: No build is currently in progress
currently_building_session: rio.Session | None = None


# This counter is increased each time a component is built. It can thus be used to
# uniquely identify the build generation of every component.
build_generation: int = 0
