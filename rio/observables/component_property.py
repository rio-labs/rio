from __future__ import annotations

import typing as t

import rio

from .observable_property import ObservableProperty

__all__ = ["ComponentProperty"]


class ComponentProperty(ObservableProperty["rio.Component"]):
    """
    ObservableProperty implementation for Rio components. Tracks some additional
    information required for reconciliation, which is unique to components.
    """

    def _get_affected_sessions(
        self, instance: rio.Component
    ) -> t.Iterable[rio.Session]:
        return [instance._session_]

    def _on_value_change(self, component: rio.Component) -> None:
        super()._on_value_change(component)
        component._properties_assigned_after_creation_.add(self.name)
