import rio

from .. import components as comps

# TODO


# <component>
class SamplePage(rio.Component):
    def build(self) -> rio.Component:
        return comps.SampleComponent()


# </component>
