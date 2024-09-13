from ...components.fundamental_component import FundamentalComponent

__all__ = ["ComponentPicker"]


class ComponentPicker(FundamentalComponent):
    """
    Lets the user select a component in the ComponentTree by clicking on it in
    the DOM.

    ## Metadata

    `public`: False
    """


ComponentPicker._unique_id_ = "ComponentPicker-builtin"
