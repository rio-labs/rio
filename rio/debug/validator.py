from __future__ import annotations

import collections
import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import *  # type: ignore

from uniserde import Jsonable, JsonDoc

import rio

from .. import inspection

__all__ = [
    "ClientComponent",
    "ValidationError",
    "Validator",
]


@dataclass
class ClientComponent:
    id: int
    type: str
    state: JsonDoc

    @classmethod
    def from_json(
        cls,
        id: int,
        delta_state: JsonDoc,
        registered_html_components: set[str],
    ) -> "ClientComponent":
        # Don't modify the original dict
        delta_state = copy.deepcopy(delta_state)

        # Get the component type
        try:
            type = delta_state.pop("_type_")
        except KeyError:
            raise ValidationError(
                f"Component with id `{id}` is missing `_type_` field"
            )

        if not isinstance(type, str):
            raise ValidationError(
                f"Component with id `{id}` has non-string type `{type}`"
            )

        if (
            type
            not in inspection.get_child_component_containing_attribute_names_for_builtin_components()
            and type not in registered_html_components
        ):
            raise ValidationError(
                f"Component with id `{id}` has unknown type `{type}`"
            )

        # Construct the result
        return cls(
            id=id,
            type=type,
            state=delta_state,
        )

    def _get_child_attribute_names(self) -> Iterable[str]:
        child_attr_names = inspection.get_child_component_containing_attribute_names_for_builtin_components()
        try:
            return child_attr_names[self.type]
        except KeyError:
            return tuple()  # TODO: How to get the children of HTML components?

    @property
    def non_child_containing_properties(
        self,
    ) -> JsonDoc:
        child_attribute_names = self._get_child_attribute_names()

        result = {}
        for name, value in self.state.items():
            if name in child_attribute_names:
                continue

            result[name] = value

        return result

    @property
    def child_containing_properties(
        self,
    ) -> dict[str, None | int | list[int]]:
        child_attribute_names = self._get_child_attribute_names()

        result = {}
        for name, value in self.state.items():
            if name not in child_attribute_names:
                continue

            result[name] = value

        return result

    @property
    def referenced_child_ids(self) -> Iterable[int]:
        for property_value in self.child_containing_properties.values():
            if property_value is None:
                continue

            if isinstance(property_value, int):
                yield property_value
                continue

            assert isinstance(property_value, list), property_value
            yield from property_value

    def __str__(self) -> str:
        # For placeholders, include the python type
        if self.type == "Placeholder":
            component_type = f'{self.type} ({self.state["_python_type_"]})'
        else:
            component_type = self.type

        return f"{component_type} #{self.id}"


class ValidationError(Exception):
    pass


class Validator:
    def __init__(
        self,
        sess: rio.Session,
        *,
        dump_directory_path: Path | None = None,
    ):
        self.session = sess

        if dump_directory_path is not None:
            assert dump_directory_path.exists(), dump_directory_path
            assert dump_directory_path.is_dir(), dump_directory_path

        self.dump_directory_path = dump_directory_path

        self.root_component: ClientComponent | None = None
        self.components_by_id: dict[int, ClientComponent] = {}

        # HTML components must be registered with the frontend before use. This set
        # contains the ids (`FundamentalComponent._unique_id`) of all registered components.
        self.registered_html_components: set[str] = set(
            inspection.get_child_component_containing_attribute_names_for_builtin_components().keys()
        )

    def dump_message(
        self,
        msg: Jsonable,
        *,
        incoming: bool,
    ):
        """
        Dump the message to a JSON file.

        If no path is set in the validator, this function does nothing.
        """
        if self.dump_directory_path is None:
            return

        direction = "incoming" if incoming else "outgoing"
        path = self.dump_directory_path / f"message-{direction}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(msg, f, indent=4)

    def dump_client_state(
        self,
        component: ClientComponent | None = None,
        path: Path | None = None,
    ) -> None:
        """
        Dump the client state to a JSON file.

        If no component is specified, the root component is used.

        If no path is used the Validator's `dump_client_state_path` is used. If
        no path is used and no path set in the validator, this function does
        nothing.
        """
        if path is None and self.dump_directory_path is not None:
            path = self.dump_directory_path / "client-state.json"

        if path is None:
            return

        if component is None:
            assert self.root_component is not None
            component = self.root_component

        with open(path, "w") as f:
            json.dump(
                self.as_json(component),
                f,
                indent=4,
                # The keys are intentionally in a legible order. Don't destroy
                # that.
                sort_keys=False,
            )

    def prune_components(self) -> None:
        """
        Remove all components which are not referenced directly or indirectly by
        the root component.
        """
        # If there is no root component, everybody is an orphan
        if self.root_component is None:
            self.components_by_id.clear()
            return

        # Find all components which are referenced directly or indirectly by the
        # root component
        visited_ids: set[int] = set()

        to_do = [self.root_component]

        while to_do:
            current = to_do.pop()

            # Use this opportunity to detect cycles
            if current.id in visited_ids:
                print(
                    f"Warning: Validator found a cycle in the component tree involving component with id `{current.id}`"
                )
                continue

            # Mark the current component as visited
            visited_ids.add(current.id)

            # Chain to its children
            for child_id in current.referenced_child_ids:
                to_do.append(self.components_by_id[child_id])

        # Remove all superfluous components
        self.components_by_id = {
            id: component
            for id, component in self.components_by_id.items()
            if id in visited_ids
        }

    def as_json(self, component: ClientComponent | None = None) -> JsonDoc:
        """
        Return a JSON-serializable representation of the client state.
        """

        if component is None:
            assert self.root_component is not None
            component = self.root_component

        result = {
            "_type_": component.type,
            "_id_": component.id,
        }

        for name, value in component.non_child_containing_properties.items():
            result[name] = value

        for name, value in component.child_containing_properties.items():
            if value is None:
                result[name] = None
                continue

            if isinstance(value, int):
                result[name] = self.as_json(self.components_by_id[value])
                continue

            assert isinstance(value, list), value
            result[name] = [
                self.as_json(self.components_by_id[id]) for id in value
            ]

        return result

    def handle_incoming_message(self, msg: Any) -> None:
        """
        Process a message passed from Client -> Server.

        This will update the `Validator`'s internal client state and validate
        the message, raising a `ValidationError` if any issues are detected.
        """

        # Delegate to the appropriate handler
        try:
            method = msg["method"]
        except KeyError:
            return

        handler_name = f"_handle_incoming_{method}"

        try:
            handler = getattr(self, handler_name)
        except AttributeError:
            return

        handler(msg["params"])

    def handle_outgoing_message(self, msg: Any) -> None:
        """
        Process a message passed from Server -> Client.

        This will update the `Validator`'s internal client state and validate
        the message, raising a `ValidationError` if any issues are detected.
        """

        # Delegate to the appropriate handler
        try:
            method = msg["method"]
        except KeyError:
            return

        handler_name = f"_handle_outgoing_{method}"

        try:
            handler = getattr(self, handler_name)
        except AttributeError:
            return

        handler(msg["params"])

    def _handle_outgoing_updateComponentStates(self, msg: Any) -> None:
        # Dump the message, if requested
        self.dump_message(msg, incoming=False)

        # Update the individual component states
        for component_id, delta_state in msg["deltaStates"].items():
            # Make sure the delta state isn't empty. While this isn't
            # technically invalid, the frontend relies on values such as the
            # margin and alignment to be present. This works, because those
            # values are generated by python regardless of whether they have
            # changed.
            required_keys = {
                "_type_",
                "_margin_",
                "_size_",
                "_align_",
                "_grow_",
            }
            missing_keys = required_keys - set(delta_state.keys())

            if missing_keys:
                delta_state_nice = json.dumps(delta_state, indent=4)
                raise ValidationError(
                    f"Delta state for with id `{component_id}` is missing required keys `{missing_keys}`. The full delta state follows:\n{delta_state_nice}"
                )

            # Get the component's existing state
            try:
                component = self.components_by_id[component_id]
            except KeyError:
                component = ClientComponent.from_json(
                    component_id,
                    delta_state,
                    self.registered_html_components,
                )
                self.components_by_id[component_id] = component
            else:
                delta_state = delta_state.copy()

                # A component's `_type_` cannot be modified. This value is also
                # stored separately by `ClientComponent`, so make sure it never
                # makes it into the component's state.
                try:
                    new_type = delta_state.pop("_type_")
                except KeyError:
                    pass
                else:
                    if new_type != component.type:
                        raise ValidationError(
                            f"Attempted to modify the `_type_` for component with id `{component_id}` from `{component.type}` to `{new_type}`"
                        ) from None

                # Update the component's state
                component.state.update(delta_state)

        # Update the root component if requested
        if msg["rootComponentId"] is not None:
            try:
                self.root_component = self.components_by_id[
                    msg["rootComponentId"]
                ]
            except KeyError:
                raise ValidationError(
                    f"Attempted to set root component to unknown component with id `{msg['rootComponentId']}`"
                ) from None

        # If no root component is known yet, this message has to contain one
        if self.root_component is None:
            raise ValidationError(
                "Despite no root component being known yet, an `UpdateComponentStates` message was sent without a `root_component_id`",
            )

        # Make sure no invalid component references are present
        invalid_references = collections.defaultdict(list)
        for component in self.components_by_id.values():
            for child_id in component.referenced_child_ids:
                if child_id not in self.components_by_id:
                    invalid_references[component.id].append(child_id)

        if invalid_references:
            invalid_references = {
                str(self.components_by_id[component_id]): child_ids
                for component_id, child_ids in invalid_references.items()
            }
            raise ValidationError(
                f"Invalid component references detected: {invalid_references}"
            )

        # Prune the component tree
        self.prune_components()

        # Look for any components which were sent in the message, but are not
        # actually used in the component tree
        ids_sent = set(msg["deltaStates"].keys())
        ids_existing = set(self.components_by_id.keys())
        ids_superfluous = sorted(ids_sent - ids_existing)

        if ids_superfluous:
            print(
                f"Validator Warning: Message contained superfluous component ids:"
            )

            for id in ids_superfluous:
                delta_state = msg["deltaStates"][id]
                print(
                    f'-  {delta_state.get("_type_", "unknown type")} #{id}  -  {delta_state}'
                )

        # Dump the client state if requested
        self.dump_client_state()

    def _handle_outgoing_evaluateJavascript(self, msg: Any):
        # Is this message registering a new component class?
        match = re.search(
            r"window.componentClasses\['(.*)'\]", msg["javaScriptSource"]
        )

        if match is None:
            return

        # Remember the component class as registered
        self.registered_html_components.add(match.group(1))
