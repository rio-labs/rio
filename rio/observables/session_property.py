from __future__ import annotations

import rio

__all__ = ["SessionProperty"]


class SessionProperty:
    def __set_name__(self, owner: type, name: str):
        self.name = name

    def __get__(
        self, session: rio.Session, owner: type | None = None
    ) -> object:
        return vars(session)[self.name]

    def __set__(self, session: rio.Session, value: object):
        vars(session)[self.name] = value
        session._changed_properties[session].add(self.name)
