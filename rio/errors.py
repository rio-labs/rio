class NoFileSelectedError(Exception):
    pass


class AssetError(Exception):
    """
    Raised when an error occurs related to assets.

    Signifies that some operation related to assets has failed. E.g. trying to
    access a nonexistent asset.
    """

    def __init__(self, message: str):
        super().__init__(message)

    @property
    def message(self) -> str:
        """
        A human-readable message describing the problem.
        """
        return self.args[0]


class NavigationFailed(Exception):
    """
    Raised when navigation to a page fails.

    This exception is raised when attempting to navigate to a page, but the
    navigation fails for some reason. This could happen, for example, because a
    page guard throws an exception.

    Note that navigating to a nonexistent pages is not an error, as `PageViews`
    will simply display their fallback in that case. Thus this exception will
    not be raised in that case.
    """

    pass
