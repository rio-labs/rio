from __future__ import annotations

import typing as t

import rio

from .observable_property import ObservableProperty

__all__ = ["SessionProperty"]


class SessionProperty(ObservableProperty["rio.Session"]):
    def __set_name__(self, owner: type, name: str):
        self.name = name

    def _get_affected_sessions(
        self, session: rio.Session
    ) -> t.Iterable[rio.Session]:
        return [session]
