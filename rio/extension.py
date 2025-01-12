import abc
import typing as t

import rio

__all__ = [
    "Extension",
]


class Extension(abc.ABC):
    """
    Base class for all Rio extensions.

    Rio extensions/plugins are classes that extend the functionality of Rio
    beyond what the core library provides. Extensions are Python classes, that
    inherit from `rio.Extension`, and are registered with the Rio app before it
    is run. They allow you to e.g. add additional pages, log system resources as
    new users connect/disconnect, and more.

    Methods in extensions can be decorated with one of the events defined in
    `rio.extension_event.*`, such as `rio.extension_event.on_session_start`.
    Those functions will then be called whenever the event occurs - in this
    case, when a user visits the app.

    ## Examples

    This minimal extension will log a message whenever a user visits or leaves
    the app:

    ```py
    # This can be any component. This one just displays a text
    class MyRoot(rio.Component):
        def build(self) -> rio.Component:
            return rio.Text(
                "Hello, World!",
                align_x=0.5,
                align_y=0.5,
            )

    # The extension itself. It has an event handler for when a session starts
    # and one for when a session ends. They both print a simple message to the
    # console when they are called. You can modify these to do anything you'd
    # like - connect to a database, change the app's default attachments,
    # whatever.
    class MyExtension(rio.Extension):
        @rio.extension_event.on_session_start
        def on_session_start(
            self,
            event: rio.ExtensionSessionStartEvent,
        ) -> None:
            print("Extension: Session started")

        @rio.extension_event.on_session_close
        def on_session_close(
            self,
            event: rio.ExtensionSessionCloseEvent,
        ) -> None:
            print("Extension: Session closed")


    # Instantiate the app and add the extension to it
    app = rio.App(
        build=MyRoot,
        extensions=[
            MyExtension(),
        ],
    )
    ```

    ## Metadata

    `public`: False
    """

    _rio_on_app_start_event_handlers_: t.ClassVar[
        list[t.Callable[[rio.extension_event.ExtensionAppStartEvent], None]]
    ]

    _rio_on_app_close_event_handlers_: t.ClassVar[
        list[t.Callable[[rio.extension_event.ExtensionAppCloseEvent], None]]
    ]

    _rio_on_session_start_event_handlers_: t.ClassVar[
        list[t.Callable[[rio.extension_event.ExtensionSessionStartEvent], None]]
    ]

    _rio_on_session_close_event_handlers_: t.ClassVar[
        list[t.Callable[[rio.extension_event.ExtensionSessionCloseEvent], None]]
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
