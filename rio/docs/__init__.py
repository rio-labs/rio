import rio

from . import custom as custom


def get_documentation_fragment(object_name: str) -> str:
    """
    Returns the fragment part of the URL corresponding to the documentation for
    the given Rio object.
    """
    return object_name.lower()


def build_documentation_url(
    object_name: str,
    *,
    relative: bool = False,
) -> rio.URL:
    """
    Returns the URL to the documentation for the given Rio object. This doesn't
    perform any checks on whether the object actually exists and has
    documentation. It relies solely on the passed values.
    """

    # Build the relative URL
    result_string = f"/docs/api/{get_documentation_fragment(object_name)}"

    # Make it absolute, if requested
    if not relative:
        result_string = "https://rio.dev" + result_string

    # Done
    return rio.URL(result_string)
