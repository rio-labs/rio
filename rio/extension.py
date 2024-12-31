import abc
import typing as t

from . import extension_event

__all__ = [
    "Extension",
]


class Extension(abc.ABC):
    _rio_on_app_start_event_handlers_: t.ClassVar[
        list[t.Callable[[extension_event.ExtensionAppStartEvent], None]]
    ]

    _rio_on_app_close_event_handlers_: t.ClassVar[
        list[t.Callable[[extension_event.ExtensionAppCloseEvent], None]]
    ]

    _rio_on_session_start_event_handlers_: t.ClassVar[
        list[t.Callable[[extension_event.ExtensionSessionStartEvent], None]]
    ]

    _rio_on_session_close_event_handlers_: t.ClassVar[
        list[t.Callable[[extension_event.ExtensionSessionCloseEvent], None]]
    ]

    def __init__(self) -> None:
        pass

    @property
    def name(self) -> str:
        """
        A human-readable name for the extension.

        Returns the name of the extension. This is sometimes used when referring
        to the plugin, for example in an admin interface that lists all active
        plugins in an app.

        Override this to change your extension's name.
        """
        # By default, derive one
        name = self.__class__.__name__
        name = name.removesuffix("Extension")
        return name

    @property
    def description(self) -> str:
        """
        A detailed description of the extension.

        Returns a description of the extension. This is sometimes used when
        referring to the plugin, for example in an admin interface that lists
        all active plugins in an app.

        Override this to change your extension's description.
        """
        return ""

    @property
    def icon(self) -> str:
        """
        A visual icon for the extension.

        Returns the icon of the extension, in standard Rio notation, for example
        `"material/extension"`. This is sometimes used when referring to the
        plugin, for example in an admin interface that lists all active plugins
        in an app.

        Override this to change your extension's icon.
        """
        # TODO: Shouldn't this return a path, asset or similar? Seems unlikely
        # that plugins just want to use material icons.

        return "material/extension"
