from __future__ import annotations

import copy
from dataclasses import field
from typing import *  # type: ignore

import uniserde
from typing_extensions import Self

from .dataclass import RioDataclassMeta, all_class_fields
from . import inspection, session

__all__ = [
    "UserSettings",
]


class UserSettings(metaclass=RioDataclassMeta):
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
        default_attachments=[
            MySettings(),
        ],
    )
    ```

    You can modify the settings from anywhere in your app. Rio will detect
    changes and persist them automatically:

    ```python
    # ... somewhere in your code
    settings = self.session[MySettings]

    # Read any values you need to
    print(settings.language)  # "en"

    # Assignments will be automatically detected and saved
    settings.language = "de"
    ```

    Warning: Since settings are stored on the user's device, special
    considerations apply. Some countries have strict privacy laws regulating
    what you can store with/without the user's consent. Make sure you are
    familiar with the legal situation before going wild and storing everything
    you can think of.

    Warning: Since settings are stored on the user's device, you should never
    trust them to be valid. A malicious actor could modify them to intentionally
    trigger bugs in your app. Always validate the values before using them.

    ## Attributes

    `section_name`: If provided, the settings file will contain a section with
        this name. This allows you to keep the configuration file organized.
        If `None`, the settings will be stored outside of any section.
    """

    # Any values from this class will be stored in the configuration file under
    # this section. This has to be set to a string. If empty, the values will be
    # set outside of any sections.
    section_name: ClassVar[str] = ""

    _rio_session_: session.Session | None = field(
        default=None, init=False, repr=False, compare=False
    )

    # Set of field names that have been modified and need to be saved
    _rio_dirty_attribute_names_: set[str] = field(
        default_factory=set, init=False, repr=False, compare=False
    )

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls.section_name.startswith("section:"):
            raise ValueError(f"Section names may not start with 'section:'")

    @classmethod
    def _from_json(
        cls,
        settings_json: dict[str, object],
        defaults: Self,
    ) -> Self:
        # Create the instance for this attachment. Bypass the constructor so
        # the instance doesn't immediately try to synchronize with the
        # frontend.
        self = object.__new__(cls)
        settings_vars = vars(self)

        if cls.section_name:
            section = cast(
                dict[str, object],
                settings_json.get("section:" + cls.section_name, {}),
            )
        else:
            section = settings_json

        annotations = inspection.get_resolved_type_annotations(cls)

        for field_name, field_type in annotations.items():
            # Skip internal fields
            if field_name in UserSettings.__annotations__:
                continue

            # Try to parse the field value
            try:
                field_value = uniserde.from_json(
                    section[field_name],
                    field_type,
                )
            except (KeyError, uniserde.SerdeError):
                field_value = copy.deepcopy(getattr(defaults, field_name))

            # Set the field value
            settings_vars[field_name] = field_value

        return self

    # This function kinda ruins linting, so we'll hide it from the IDE
    def __setattr(self, name: str, value: Any) -> None:
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

    if not TYPE_CHECKING:
        __setattr__ = __setattr

    def _equals(self, other: Self) -> bool:
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
