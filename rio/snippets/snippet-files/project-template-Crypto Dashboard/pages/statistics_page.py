import rio

# <additional-imports>
from .. import components as comps

# </additional-imports>


# <component>
@rio.page(
    name="Statistics",
    url_segment="statistics",
)
class TransactionPage(rio.Component):
    """
    HELP US IMPROVE THIS TEMPLATE
    """

    def build(self) -> rio.Component:
        return comps.ContributionWanted(
            align_x=0.5,
            align_y=0.5,
            grow_x=True,
        )


# </component>
