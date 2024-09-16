from __future__ import annotations

from typing import *  # type: ignore

import rio

# <additional-imports>
from .. import components as comps
from .. import data_models

# </additional-imports>


# <component>
def guard(event: rio.GuardEvent) -> str | None:
    # This website allows access to sensitive information. Enforce stringent
    # access control to all in-app pages.

    # Is the user logged in? Fetch the `UserInformation` is logged in
    try:
        event.session[data_models.LoggedInUser]

    # Not logged in, navigate to the login page
    except KeyError:
        return ""
        # return "/login"

    return None


@rio.page(name="App", url_segment="app", guard=guard)
class InnerAppPage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Column(
            comps.Navbar(),
            rio.PageView(
                fallback_build=comps.NoSuchPage,
                grow_y=True,
            ),
        )


# </component>
