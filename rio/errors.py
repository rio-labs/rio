class NoFileSelectedError(Exception):
    """
    Raised when the user doesn't select a file.

    This exception is raised when the user is prompted to select a file with a
    file picker and they close the file picker without selecting a file. This is
    a perfectly valid operation on the user's end - make sure you handle it.
    """

    pass


class AssetError(Exception):
    """
    Raised when an error occurs related to assets.

    Signifies that some operation related to assets has failed. E.g. trying to
    access a nonexistent asset.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)

    @property
    def message(self) -> str:
        """
        A human-readable message describing the problem.

        This message contains additional information about the error to inform
        the developer.
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


class ClipboardError(Exception):
    """
    Raised for errors related to clipboard operations.

    This exception is raised when an error occurs while trying to interact with
    the clipboard. For example when trying to read from the clipboard and the
    browser refuses due to privacy restrictions.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)

    @property
    def message(self) -> str:
        """
        Returns the error message as a string.

        This message contains additional information about the error in a form
        amenable to being displayed to humans.
        """
        return self.args[0]


class InvalidProjectConfigError(Exception):
    """
    Raised when the project configuration is invalid.

    This exception is raised when a function cannot continue due to a problem
    with the project configuration. For example, the project's `rio.toml` could
    be invalid TOML, or not exist at all.

    ## Metadata

    `public`: False
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)

    @property
    def message(self) -> str:
        """
        Returns the error message as a string.
        """
        return self.args[0]
