import rio

# <additional imports>
from ... import components as comps

# </additional imports>


# <component>
@rio.page(
    name="Members",
    url_segment="members",
)
class MembersPage(rio.Component):
    """
    This page allows users to manage access by inviting new members via email.
    """

    def build(self) -> rio.Component:
        return rio.Column(
            comps.ContentContainer(
                "Manage access",
                "Invite new members by email address.",
                add_separator=False,
            ),
            rio.Button(
                "Invite people",
                shape="rounded",
                color=rio.Color.WHITE,
                # TODO: Add an event handler to open the invite dialog
                align_y=0.5,
                align_x=0,
            ),
            spacing=1.5,
            align_y=0,
        )


# </component>
