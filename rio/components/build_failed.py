from uniserde import JsonDoc

from .fundamental_component import FundamentalComponent

__all__ = ["BuildFailed"]


class BuildFailed(FundamentalComponent):
    """
    Used as a placeholder in case a component's `build` function throws an
    error.


    ## Metadata

    public: False
    """

    error_summary: str
    error_details: str

    # Debug details can contain sensitive information. Sending these to the
    # client is fine during development, but mustn't happen in production.
    def _custom_serialize(self) -> JsonDoc:
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


BuildFailed._unique_id = "BuildFailed-builtin"
