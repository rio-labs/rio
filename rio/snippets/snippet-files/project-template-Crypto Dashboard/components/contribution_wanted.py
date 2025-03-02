import rio

# <additional-imports>
from .. import data_models

# </additional-imports>


# <component>
class ContributionWanted(rio.Component):
    """
    The ContributionWanted class is a component of a dashboard application, designed to
    display a message for contributors.

    ## Attributes

    `message`: The message for contributors.
    """

    def build(self) -> rio.Component:
        """
        Creates a message for contributors.
        """
        # Set the margin and minimum width based on the device
        device = self.session[data_models.PageLayout].device

        if device == "desktop":
            margin = 5
            min_width = 40
        else:
            margin = 2
            min_width = self.session.window_width - 2

        return rio.Card(
            rio.Markdown(
                """
# Contribution Wanted! :)
                
Would you like to help us improve this template or share your ideas? Feel free
to get in touch through this [GitHub
issue](https://github.com/rio-labs/rio/issues/215). # TODO: get correct issue when open

""",
                margin=margin,
            ),
            min_width=min_width,
        )


# </component>
