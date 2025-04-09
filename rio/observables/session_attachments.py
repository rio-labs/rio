from __future__ import annotations

import typing as t

from .. import global_state, session, user_settings_module
from . import dataclass

__all__ = ["SessionAttachments"]


T = t.TypeVar("T")


class SessionAttachments:
    def __init__(self, sess: session.Session) -> None:
        self._session = sess
        self._attachments: dict[type, object] = {}

    def __iter__(self) -> t.Iterator[object]:
        return iter(self._attachments.values())

    def __contains__(self, typ: type) -> bool:
        return typ in self._attachments

    def __getitem__(self, typ: type[T]) -> T:
        global_state.accessed_items[self._session].add(typ)

        try:
            return self._attachments[typ]  # type: ignore
        except KeyError:
            raise KeyError(typ) from None

    def _add(self, value: object, synchronize: bool) -> None:
        cls = type(value)

        self._session._changed_items[self._session].add(cls)
        self._session._refresh_required_event.set()

        # If the value isn't a UserSettings instance, just assign it and we're
        # done
        if not isinstance(value, user_settings_module.UserSettings):
            self._attachments[cls] = value
            return

        # If a UserSettings object is already attached, unlink it from the
        # session
        try:
            old_value = t.cast(
                user_settings_module.UserSettings, self._attachments[cls]
            )
        except KeyError:
            pass
        else:
            old_value._rio_session_ = None

        # Save the new value with the rest of the attachments
        self._attachments[cls] = value

        # Link the new value to the session
        value._rio_session_ = self._session

        # Trigger a resync
        if synchronize:
            # Since only assignments make attributes dirty, operations like
            # `list.append()` go unnoticed. So to guarantee that everything is
            # saved, we'll explicitly mark all attributes as dirty.
            value._rio_dirty_attribute_names_ = (
                set(dataclass.all_class_fields(cls))
                - user_settings_module.UserSettings.__annotations__.keys()
            )

            self._session._save_settings_soon()

    def add(self, value: t.Any) -> None:
        self._add(value, synchronize=True)

    def remove(self, typ: type) -> None:
        # Remove the attachment, propagating any `KeyError`
        old_value = self._attachments.pop(typ)

        self._session._changed_items[self._session].add(typ)
        self._session._refresh_required_event.set()

        # User settings need special care
        if not isinstance(old_value, user_settings_module.UserSettings):
            return

        # Unlink the value from the session
        old_value._rio_session_ = None

        # Trigger a resync
        #
        # TODO: `_save_settings_soon` doesn't currently delete any settings
        self._session._save_settings_soon()
