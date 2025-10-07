from __future__ import annotations

import copy
import typing as t

import imy.docstrings
import introspection.typing
import typing_extensions as te
import uniserde

from . import inspection, serialization, session
from .observables.dataclass import Dataclass, all_class_fields, internal_field

__all__ = ["UserSettings", "HttpOnly"]


T = te.TypeVar("T")
HTTP_ONLY = "rio.HttpOnly"
HttpOnly = te.Annotated[T, HTTP_ONLY]


@imy.docstrings.mark_constructor_as_private  # Don't document the constructor
class UserSettings(Dataclass):
    """
    Base class for persistent user settings.

    When creating an app or website you'll often want to store some values so
    that you can access them the next time the user visits your app. A typical
    example are configuration values set by the user - you wouldn't want to ask
    for these every time.

    Rio makes it easy to store and retrieve such values. Create a class that
    inherits from `UserSettings`, and attach it to the `Session`. That's it! Rio
    will automatically store and retrieve the values for you.

    ```python
    # Create a dataclass that inherits from rio.UserSettings. This indicates to
    # Rio that these are settings and should be persisted.
    class MySettings(rio.UserSettings):
        language: str = "en"

    # Attach the settings to the app. This way the settings will be available in
    # all sessions. They will be loaded automatically from the user whenever
    # they connect or start the app.
    app = rio.App(
        ...,
        default_attachments=[MySettings()],
    )
    ```

    You can modify the settings from anywhere in your app. Just make sure to
    reattach them to the session to persist the changes:

    ```python
    # ... somewhere in your code
    settings = self.session[MySettings]

    # Read any values you need to
    print(settings.language)  # "en"

    # Update the settings
    settings.language = "de"

    # Reattach the settings to the session to persist the changes
    self.session.attach(settings)
    ```

    To protect against malicious Javascript code stealing sensitive data, you
    can use the type annotation `rio.HttpOnly`. Settings marked as `HttpOnly`
    will be stored in http-only cookies.

    ```python
    class LoginInformation(rio.UserSettings):
        session_token: rio.HttpOnly[str | None] = None
    ```

    Don't overuse this though, since most browsers only support up to 4kB of
    cookies.

    Warning: Since settings are stored on the user's device, special
        considerations apply. Some countries have strict privacy laws regulating
        what you can store with/without the user's consent. Make sure you are
        familiar with the legal situation before going wild and storing
        everything you can think of.

    Warning: Since settings are stored on the user's device, you should never
        trust them to be valid. A malicious actor could modify them to
        intentionally trigger bugs in your app. Always validate the values
        before using them.

    ## Attributes

    `section_name`: If provided, the settings file will contain a section with
        this name. This allows you to keep the configuration file organized.
        If `None`, the settings will be stored outside of any section.
    """

    # TODO: Document which datatypes are supported

    # Any values from this class will be stored in the configuration file under
    # this section. This has to be set to a string. If empty, the values will be
    # set outside of any sections.
    section_name: t.ClassVar[str] = ""

    _rio_attrs_to_save_as_cookies_: t.ClassVar[set[str]]

    _rio_session_: session.Session | None = internal_field(default=None)

    # Set of field names that have been modified and need to be saved
    _rio_dirty_attribute_names_: set[str] = internal_field(default_factory=set)

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls.section_name.startswith("section:"):
            raise ValueError("Section names may not start with 'section:'")

        cls._rio_attrs_to_save_as_cookies_ = {
            field_name
            for field_name, field_type in inspection.get_resolved_type_annotations(
                cls
            ).items()
            if HTTP_ONLY
            in introspection.typing.TypeInfo(field_type).annotations
        }

    @classmethod
    def _from_json(
        cls,
        localstorage_sections: dict[str, uniserde.JsonDoc],
        cookie_sections: dict[str, uniserde.JsonDoc],
        defaults: te.Self,
    ) -> te.Self:
        # Create the instance for this attachment. Bypass the constructor so the
        # instance doesn't immediately try to synchronize with the frontend.
        self = object.__new__(cls)
        settings_vars = vars(self)

        # Grab the relevant sections from the input dicts
        localstorage_section = localstorage_sections.get(cls.section_name, {})
        cookie_section = cookie_sections.get(cls.section_name, {})

        annotations = inspection.get_resolved_type_annotations(cls)

        for field_name, field_type in annotations.items():
            # Skip internal fields
            if field_name in UserSettings.__annotations__:
                continue

            # Try to parse the field value
            try:
                if field_name in cls._rio_attrs_to_save_as_cookies_:
                    json_value = cookie_section[field_name]
                else:
                    json_value = localstorage_section[field_name]

                field_value = serialization.json_serde.from_json(
                    field_type, json_value
                )
            except (KeyError, uniserde.SerdeError):
                field_value = copy.deepcopy(getattr(defaults, field_name))

            # Set the field value
            settings_vars[field_name] = field_value

        return self

    # This function kinda ruins linting, so we'll hide it from the IDE
    def __setattr(self, name: str, value: t.Any) -> None:
        # These attributes doesn't exist yet during the constructor
        dct = vars(self)
        dirty_attribute_names = dct.setdefault(
            "_rio_dirty_attribute_names_", set()
        )

        # Set the attribute
        dct[name] = value

        # Ignore assignments to internal attributes
        if name in __class__.__annotations__:
            return

        # Mark it as dirty
        dirty_attribute_names.add(name)

        # Make sure a write back task is running
        # if self._rio_session_ is not None:
        #     self._rio_session_._save_settings_soon()

    if not t.TYPE_CHECKING:
        __setattr__ = __setattr

    def _equals(self, other: te.Self) -> bool:
        if type(self) != type(other):
            return False

        fields_to_compare = (
            all_class_fields(type(self)).keys()
            - all_class_fields(__class__).keys()
        )
        for field_name in fields_to_compare:
            if getattr(self, field_name) != getattr(other, field_name):
                return False

        return True

    # This method is inherited from dataclasses but not meant to be public
    #
    # TODO: Currently, settings are only saved when they're (re-)attached to the
    # session. Originally we wanted to save them automatically after every
    # change, but we could only detect assignments (like `settings.foo = bar`)
    # and not mutations (like `settings.foos.append(bar)`), so it was very
    # unreliable. Now that we've added observable data structures (`rio.List`,
    # etc.) we should revisit this. Then we can also make this `bind()` method
    # public - as long as attribute bindings correctly trigger a save, of
    # course.
    @te.override
    def bind(self, *args, **kwargs) -> t.NoReturn:
        """
        ## Metadata

        `public`: False
        """

        raise AttributeError()
