from __future__ import annotations

from pathlib import Path

from identity_containers import IdentityDefaultDict, IdentitySet

import rio

from .components import component

# This boolean indicates whether the program was started via `rio run`. This
# lets us display more useful error messages if the user tries to execute
# something like `app.run_in_window()`, which conflicts with `rio run`.
launched_via_rio_run: bool = False


# When launched via `rio run`, the usual ways to detect the "main file" (`import
# __main__` and `sys.argv`) don't work. So `rio run` explicitly tells us what
# the "main file" is by setting this variable.
rio_run_app_module_path: Path | None = None


# Before a component is built, this variable is set to that component. This
# allows newly created components to determine their creator, as well as
# session.
#
# - `Component`: The component that is currently being built
# - `None`: The build method of the app itself is currently being called
currently_building_component: rio.Component | None = None


# Same as `currently_building_component`, but holding that component's session.
#
# - `Session`: The session that owns the currently building component
# - `None`: No build is currently in progress
currently_building_session: rio.Session | None = None


# Keeps track of components that have a `key` (and were instantiated during this
# `build`). The reconciler needs to know about every component with a `key`, and
# this is the fastest way to do it.
key_to_component: dict[component.Key, rio.Component] = {}


# These keep track of attributes, items, and objects that have been accessed.
# (Typically these are reset before a `build` function is called)
accessed_objects = IdentitySet[object]()
accessed_attributes = IdentityDefaultDict[object, set[str]](set)
accessed_items = IdentityDefaultDict[object, IdentitySet[object]](
    IdentitySet[object]
)
