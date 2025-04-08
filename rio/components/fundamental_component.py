from __future__ import annotations

import json
import typing as t

from uniserde import Jsonable, JsonDoc

import rio

from .. import inspection, utils
from .component import Component

__all__ = ["FundamentalComponent"]


JAVASCRIPT_SOURCE_TEMPLATE = """
// Run the code in a function to avoid name clashes with globals
(function () {

    %(js_source)s


    // Make sure the user has defined the expected class.
    if (typeof %(js_user_class_name)s === 'undefined') {
        let message = `Failed to register component with unique ID \\`%(cls_unique_id)s\\` because its JavaScript source has not defined the expected class \\`%(js_user_class_name)s\\``;
        console.error(message);
        throw new Error(message);
    }


    // Wrap it in a class which inherits from Rio's ComponentBase
    class %(js_wrapper_class_name)s extends window.RIO_COMPONENT_BASE {
        createElement() {
            this.userInstance = new %(js_user_class_name)s();
            this.userInstance.__rioWrapper__ = this;
            let element = this.userInstance.createElement();
            this.userInstance.element = element;
            return element;
        }

        updateElement(deltaState, latentComponents) {
            this.userInstance.updateElement(deltaState);
        }
    }

    // Expose additional functionality to the user
    %(js_user_class_name)s.prototype.state = function () {
        return this.__rioWrapper__.state;
    }

    // Register the component
    window.COMPONENT_CLASSES['%(cls_unique_id)s'] = %(js_wrapper_class_name)s;
    window.CHILD_ATTRIBUTE_NAMES['%(cls_unique_id)s'] = %(child_attribute_names)s;
})();

"""


CSS_SOURCE_TEMPLATE = """
const style = document.createElement('style');
style.innerHTML = %(escaped_css_source)s;
document.head.appendChild(style);
"""


class FundamentalComponent(Component):
    # Unique id for identifying this class in the frontend. This is initialized
    # in `__init_subclass__`.
    _unique_id_: t.ClassVar[str]

    def build(self) -> rio.Component:
        raise RuntimeError(
            f"Attempted to call `build` on `FundamentalComponent` {self}"
        )

    @classmethod
    def build_javascript_source(cls, sess: rio.Session) -> str:
        """
        ## Metadata

        `public`: False
        """
        return ""

    @classmethod
    def build_css_source(cls, sess: rio.Session) -> str:
        """
        ## Metadata

        `public`: False
        """
        return ""

    def __init_subclass__(cls) -> None:
        # Assign a unique id to this class. This allows the frontend to identify
        # components.
        hash_ = utils.secure_string_hash(
            cls.__module__,
            cls.__qualname__,
            hash_length=12,
        )

        cls._unique_id_ = f"{cls.__name__}-{hash_}"

        # Chain up
        super().__init_subclass__()

    @classmethod
    async def _initialize_on_client(cls, sess: rio.Session) -> None:
        message_source = ""

        javascript_source = cls.build_javascript_source(sess)
        if javascript_source:
            message_source += JAVASCRIPT_SOURCE_TEMPLATE % {
                "js_source": javascript_source,
                "js_user_class_name": cls.__name__,
                "js_wrapper_class_name": f"{cls.__name__}Wrapper",
                "cls_unique_id": cls._unique_id_,
                "child_attribute_names": json.dumps(
                    inspection.get_child_component_containing_attribute_names(
                        cls
                    )
                ),
            }

        css_source = cls.build_css_source(sess)
        if css_source:
            escaped_css_source = json.dumps(css_source)
            message_source += CSS_SOURCE_TEMPLATE % {
                "escaped_css_source": escaped_css_source,
            }

        if message_source:
            await sess._evaluate_javascript(message_source)

    async def _on_message_(self, message: Jsonable, /) -> None:
        """
        This function is called when the frontend sends a message to this
        component via `sendMessage`.
        """
        raise AssertionError(
            f"Frontend sent an unexpected message to a `{type(self).__name__}`"
        )

    def _validate_delta_state_from_frontend(self, delta_state: JsonDoc) -> None:
        """
        This function is called to check whether the delta state received from
        the frontend is valid. If the frontend tries to change the state in a
        way that isn't allowed, this function should throw an error.
        """
        raise AssertionError(
            f"Frontend tried to change the state of a `{type(self).__name__}`"
        )

    async def _call_event_handlers_for_delta_state(
        self, delta_state: JsonDoc
    ) -> None:
        pass

    def _apply_delta_state_from_frontend(
        self, delta_state: dict[str, t.Any]
    ) -> None:
        """
        Applies the delta state received from the frontend without marking the
        component as dirty.
        """
        # Since the new state is coming from JS, we know two things:
        # 1. There's no need to send the state back to JS
        # 2. There's no need to re-build this component, since it's a
        #    FundamentalComponent
        # That means we should avoid marking this component as dirty.
        dirty_properties = set(self.session._changed_attributes[self])

        # Update all state properties to reflect the new state
        for attr_name, attr_value in delta_state.items():
            setattr(self, attr_name, attr_value)

        self.session._changed_attributes[self] = dirty_properties
