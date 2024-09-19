from uniserde import JsonDoc

from .fundamental_component import FundamentalComponent

__all__ = ["ErrorPlaceholder"]


class ErrorPlaceholder(FundamentalComponent):
    """
    Used as a placeholder in case the real component isn't available for
    whatever reason. For example:

    - When a `build` function throws an error
    - When a page can't be imported


    ## Metadata

    `public`: False
    """

    error_summary: str
    error_details: str

    # Debug details can contain sensitive information. Sending these to the
    # client is fine during development, but mustn't happen in production.
    def _custom_serialize_(self) -> JsonDoc:
        if self.session._app_server.debug_mode:
            return {
                "_rio_internal_": True,
            }
        else:
            return {
                "error_summary": "This component has crashed",
                "error_details": "",
                "_rio_internal_": True,
            }


ErrorPlaceholder._unique_id_ = "ErrorPlaceholder-builtin"
