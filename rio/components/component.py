from __future__ import annotations

import abc
import asyncio
import inspect
import io
import sys
import typing
import weakref
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import KW_ONLY, field
from pathlib import Path
from typing import *  # type: ignore

import introspection
from typing_extensions import Self, dataclass_transform
from uniserde import Jsonable, JsonDoc

import rio

from .. import event, global_state, inspection
from ..dataclass import RioDataclassMeta, class_local_fields, internal_field
from ..state_properties import AttributeBindingMaker, StateProperty

__all__ = ["Component"]


T = TypeVar("T")


async def call_component_handler_once(
    weak_component: weakref.ReferenceType[Component],
    handler: Callable,
) -> None:
    # Does the component still exist?
    component = weak_component()

    if component is None:
        return

    # Call the handler
    await component.call_event_handler(lambda: handler(component))
    await component.session._refresh()


async def _periodic_event_worker(
    weak_component: weakref.ReferenceType[Component],
    handler: Callable,
    period: float,
) -> None:
    try:
        sess = weak_component().session  # type: ignore
    except AttributeError:
        return

    while True:
        # Wait for the next tick
        await asyncio.sleep(period)

        # Wait until there's an active connection to the client. We won't run
        # code periodically if we aren't sure whether the client will come back.
        await sess._is_active_event.wait()

        # Call the handler
        await call_component_handler_once(weak_component, handler)


def _determine_properties_set_by_creator(
    component: Component, args: tuple, kwargs: dict
) -> set[str]:
    # Determine which properties were explicitly set. This includes
    # parameters that received an argument, and also varargs (`*args`)
    signature = inspect.signature(component.__init__)
    bound_args = signature.bind(*args, **kwargs)

    properties_set_by_creator = set(bound_args.arguments)

    # fmt: off
    properties_set_by_creator.update(
        param.name
        for param in signature.parameters.values()
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        )
    )
    # fmt: on

    # Discard parameters that don't correspond to state properties
    properties_set_by_creator.intersection_update(
        type(component)._state_properties_
    )

    return properties_set_by_creator


C = typing.TypeVar("C", bound="Component")


# For some reason vscode doesn't understand that this class is a
# `@dataclass_transform`, so we'll annotate it again...
@dataclass_transform(
    eq_default=False,
    field_specifiers=(internal_field, field),
)
class ComponentMeta(RioDataclassMeta):
    # Cache for the set of all `StateProperty` instances in this class
    _state_properties_: dict[str, StateProperty]

    # Maps event tags to the methods that handle them. The methods aren't bound
    # to the instance yet, so make sure to pass `self` when calling them
    #
    # The assigned value is needed so that the `Component` class itself has a
    # valid value. All subclasses override this value in `__init_subclass__`.
    _rio_event_handlers_: defaultdict[
        event.EventTag, list[tuple[Callable, Any]]
    ]

    # Whether this component class is built into Rio, rather than user defined,
    # or from a library.
    _rio_builtin_: bool

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Replace all properties with custom state properties
        cls._initialize_state_properties()

        # Inherit event handlers from parents
        cls._rio_event_handlers_ = defaultdict(list)

        for base in cls.__bases__:
            if not isinstance(base, ComponentMeta):
                continue

            for event_tag, handlers in base._rio_event_handlers_.items():
                cls._rio_event_handlers_[event_tag].extend(handlers)

        # Add events from this class itself
        for member in vars(cls).values():
            if not callable(member):
                continue

            try:
                events = member._rio_events_
            except AttributeError:
                continue

            for event_tag, args in events.items():
                for arg in args:
                    cls._rio_event_handlers_[event_tag].append((member, arg))

        # Is this class built into Rio?
        cls._rio_builtin_ = cls.__module__.startswith("rio.")

    def _initialize_state_properties(cls) -> None:
        """
        Spawn `StateProperty` instances for all annotated properties in this
        class.
        """
        all_parent_state_properties: dict[str, StateProperty] = {}

        for base in reversed(cls.__bases__):
            if isinstance(base, ComponentMeta):
                all_parent_state_properties.update(base._state_properties_)  # type: ignore (wtf?)

        cls._state_properties_ = all_parent_state_properties

        annotations: dict = vars(cls).get("__annotations__", {})
        module = sys.modules[cls.__module__]

        for field_name, field in class_local_fields(cls).items():
            # Skip internal fields
            if not field.state_property:
                continue

            # Create the StateProperty
            # readonly = introspection.typing.has_annotation(annotation, Readonly
            readonly = False  # TODO

            state_property = StateProperty(
                field_name, readonly, annotations[field_name], module
            )
            setattr(cls, field_name, state_property)

            # Add it to the set of all state properties for rapid lookup
            cls._state_properties_[field_name] = state_property

    @introspection.mark.does_not_alter_signature
    def __call__(cls: type[C], *args: object, **kwargs: object) -> C:
        # Inject the session before calling the constructor
        # Fetch the session this component is part of
        if global_state.currently_building_session is None:
            raise RuntimeError(
                "Components can only be created inside of `build` methods."
            )

        component: C = object.__new__(cls)  # type: ignore (wtf?)

        session = global_state.currently_building_session
        component._session_ = session

        # Create a unique ID for this component
        component._id = session._next_free_component_id
        session._next_free_component_id += 1

        component._properties_assigned_after_creation_ = set()

        # Call `__init__`
        component.__init__(*args, **kwargs)

        component._init_called_ = True

        # Some components (like `Grid`) manually mark some properties as
        # explicitly set in their `__init__`, so we must use `.update()` instead
        # of an assignment
        component._properties_set_by_creator_.update(
            _determine_properties_set_by_creator(component, args, kwargs)
        )

        # Store a weak reference to the component's creator
        if global_state.currently_building_component is None:
            component._weak_creator_ = lambda: None
        else:
            component._weak_creator_ = weakref.ref(
                global_state.currently_building_component
            )

        # Keep track of this component's existence
        #
        # Components must be known by their id, so any messages addressed to
        # them can be passed on correctly.
        session._weak_components_by_id[component._id] = component

        session._register_dirty_component(
            component,
            include_children_recursively=False,
        )

        # Some events need attention right after the component is created
        for event_tag, event_handlers in component._rio_event_handlers_.items():
            # Don't register an empty list of handlers, since that would
            # still slow down the session
            if not event_handlers:
                continue

            # Page changes are handled by the session. Register the handler
            if event_tag == event.EventTag.ON_PAGE_CHANGE:
                callbacks = tuple(handler for handler, unused in event_handlers)
                session._page_change_callbacks[component] = callbacks

            # The `periodic` event needs a task to work in
            elif event_tag == event.EventTag.PERIODIC:
                for callback, period in event_handlers:
                    session.create_task(
                        _periodic_event_worker(
                            weakref.ref(component), callback, period
                        ),
                        name=f"`rio.event.periodic` event worker for {component}",
                    )

        # Call `_rio_post_init` for every class in the MRO
        for base in reversed(type(component).__mro__):
            try:
                post_init = vars(base)["_rio_post_init"]
            except KeyError:
                continue

            post_init(component)

        component._properties_assigned_after_creation_.clear()

        return component


# Using `metaclass=ComponentMeta` makes this an abstract class, but since
# pyright is too stupid to understand that, we have to additionally inherit from
# `abc.ABC`
class Component(abc.ABC, metaclass=ComponentMeta):
    """
    Base class for all Rio components.

    Components are the building blocks of `rio` apps. `rio` ships with many
    useful components out of the box, but you can also subclass a component to
    create your own.


    ## Attributes

    `key`: A unique identifier for this component. If two components with the
        same key are present during reconciliation they will be considered
        the same component and their state will be preserved. If no key is
        specified, reconciliation falls back to a less precise method, by
        comparing the location of the component in the component tree.

    `margin`: The margin around this component. This is a shorthand for
        setting `margin_left`, `margin_top`, `margin_right` and
        `margin_bottom` to the same value. If multiple conflicting margins
        are specified the most specific one wins. If for example `margin`
        and `margin_left` are both specified, `margin_left` is used for the
        left side, while the other sides use `margin`.

    `margin_x`: The horizontal margin around this component. This is a
        shorthand for setting `margin_left` and `margin_right` to the same
        value. If multiple conflicting margins are specified the most
        specific one wins. If for example `margin_x` and `margin_left` are
        both specified, `margin_left` is used for the left side, while the
        other side uses `margin_x`.

    `margin_y`: The vertical margin around this component. This is a shorthand
        for setting `margin_top` and `margin_bottom` to the same value. If
        multiple conflicting margins are specified the most specific one
        wins. If for example `margin_y` and `margin_top` are both specified,
        `margin_top` is used for the top side, while the other side uses
        `margin_y`.

    `margin_left`: The left margin around this component. If multiple
        conflicting margins are specified this one will be used, since it's
        the most specific. If for example `margin_left` and `margin` are
        both specified, `margin_left` is used for the left side, while the
        other sides use `margin`.

    `margin_top`: The top margin around this component. If multiple
        conflicting margins are specified this one will be used, since it's
        the most specific. If for example `margin_top` and `margin` are both
        specified, `margin_top` is used for the top side, while the other
        sides use `margin`.

    `margin_right`: The right margin around this component. If multiple
        conflicting margins are specified this one will be used, since it's
        the most specific. If for example `margin_right` and `margin` are
        both specified, `margin_right` is used for the right side, while the
        other sides use `margin`.

    `margin_bottom`: The bottom margin around this component. If multiple
        conflicting margins are specified this one will be used, since it's
        the most specific. If for example `margin_bottom` and `margin` are
        both specified, `margin_bottom` is used for the bottom side, while
        the other sides use `margin`.

    `width`: How much horizontal space this component should request during
        layouting. This can be either a number, or one of the special
        values:

        - If `"natural"`, the component will request the minimum amount it
          requires to fit on the screen. For example a `Text` will request
          however much space the characters of that text require. A `Row`
          would request the sum of the widths of its children.

        - If `"grow"`, the component will request all the remaining space in its parent.

        - Please note that the space a `Component` receives during layouting
          may not match the request. As a general rule, for example, containers
          try to pass on all available space to children. If you really want a
          `Component` to only take up as much space as requested, consider
          specifying an alignment.

    `height`: How much vertical space this component should request during
        layouting. This can be either a number, or one of the special values:

        - If `"natural"`, the component will request the minimum amount it
          requires to fit on the screen. For example a `Text` will request
          however much space the characters of that text require. A `Row`
          would request the height of its tallest child.

        - If `"grow"`, the component will request all the remaining space in its
          parent.

        - Please note that the space a `Component` receives during layouting
          may not match the request. As a general rule for example, containers
          try to pass on all available space to children. If you really want a
          `Component` to only take up as much space as requested, consider
          specifying an alignment.

    `align_x`: How this component should be aligned horizontally, if it
        receives more space than it requested. This can be a number between
        0 and 1, where 0 means left-aligned, 0.5 means centered, and 1 means
        right-aligned.

    `align_y`: How this component should be aligned vertically, if it receives
        more space than it requested. This can be a number between 0 and 1,
        where 0 means top-aligned, 0.5 means centered, and 1 means
        bottom-aligned.
    """

    _: KW_ONLY
    key: str | None = internal_field(default=None, init=True)

    width: float | Literal["natural", "grow"] = "natural"
    height: float | Literal["natural", "grow"] = "natural"

    align_x: float | None = None
    align_y: float | None = None

    margin_left: float | None = None
    margin_top: float | None = None
    margin_right: float | None = None
    margin_bottom: float | None = None

    margin_x: float | None = None
    margin_y: float | None = None
    margin: float | None = None

    _id: int = internal_field(init=False)

    # Weak reference to the component's builder. Used to check if the component
    # is still part of the component tree.
    #
    # Dataclasses like to turn this function into a method. Make sure it works
    # both with and without `self`.
    _weak_builder_: Callable[[], Component | None] = internal_field(
        default=lambda *args: None,
        init=False,
    )

    # Weak reference to the component's creator
    _weak_creator_: Callable[[], Component | None] = internal_field(
        init=False,
    )

    # Each time a component is built the build generation in that component's
    # COMPONENT DATA is incremented. If this value no longer matches the value
    # in its builder's COMPONENT DATA, the component is dead.
    _build_generation_: int = internal_field(default=-1, init=False)

    _session_: rio.Session = internal_field(init=False)

    # Remember which properties were explicitly set in the constructor
    _properties_set_by_creator_: set[str] = internal_field(
        init=False, default_factory=set
    )

    # Remember which properties had new values assigned after the component's
    # construction
    _properties_assigned_after_creation_: set[str] = internal_field(init=False)

    # Whether the `on_populate` event has already been triggered for this
    # component
    _on_populate_triggered_: bool = internal_field(default=False, init=False)

    # Whether this instance is internal to Rio, e.g. because the spawning
    # component is a high-level component defined in Rio.
    #
    # In debug mode, this field is initialized by monkeypatches. When running in
    # release mode this value isn't set at all, and the default set below is
    # always used.
    _rio_internal_: bool = internal_field(init=False, default=False)

    # The stackframe which has created this component. Used by the debugger.
    # Only initialized if in debugging mode.
    _creator_stackframe_: tuple[Path, int] = internal_field(init=False)

    # Whether this component's `__init__` has already been called. Used to
    # verify that the `__init__` doesn't try to read any state properties.
    _init_called_: bool = internal_field(init=False, default=False)

    @property
    def session(self) -> rio.Session:
        """
        Return the session this component is part of.
        """
        return self._session_

    # There isn't really a good type annotation for this... Self is the closest
    # thing
    def bind(self) -> Self:
        return AttributeBindingMaker(self)  # type: ignore

    def _custom_serialize(self) -> JsonDoc:
        """
        Return any additional properties to be serialized, which cannot be
        deduced automatically from the type annotations.
        """
        return {}

    @abstractmethod
    def build(self) -> rio.Component:
        """
        Return a component tree which represents the UI of this component.

        Most components define their appearance and behavior by combining other,
        more basic components. This function's purpose is to do exactly that. It
        returns another component (typically a container) which will be
        displayed on the screen.

        The `build` function should be pure, meaning that it does not modify the
        component's state and returns the same result each time it's invoked.
        """
        raise NotImplementedError()  # pragma: no cover

    def _iter_direct_children(self) -> Iterable[Component]:
        for name in inspection.get_child_component_containing_attribute_names(
            type(self)
        ):
            try:
                value = getattr(self, name)
            except AttributeError:
                continue

            if isinstance(value, Component):
                yield value

            if isinstance(value, list):
                value = cast(list[object], value)

                for item in value:
                    if isinstance(item, Component):
                        yield item

    def _iter_direct_and_indirect_child_containing_attributes(
        self,
        *,
        include_self: bool,
        recurse_into_high_level_components: bool,
    ) -> Iterable[Component]:
        from . import fundamental_component  # Avoid circular import problem

        # Special case the component itself to handle `include_self`
        if include_self:
            yield self

        if not recurse_into_high_level_components and not isinstance(
            self, fundamental_component.FundamentalComponent
        ):
            return

        # Iteratively yield all children
        to_do = list(self._iter_direct_children())
        while to_do:
            cur = to_do.pop()
            yield cur

            if recurse_into_high_level_components or isinstance(
                cur, fundamental_component.FundamentalComponent
            ):
                to_do.extend(cur._iter_direct_children())

    def _iter_component_tree(self) -> Iterable[Component]:
        """
        Iterate over all components in the component tree, with this component as the root.
        """
        from . import fundamental_component  # Avoid circular import problem

        yield self

        if isinstance(self, fundamental_component.FundamentalComponent):
            for child in self._iter_direct_children():
                yield from child._iter_component_tree()
        else:
            build_result = self.session._weak_component_data_by_component[
                self
            ].build_result
            yield from build_result._iter_component_tree()

    async def _on_message(self, msg: Jsonable, /) -> None:
        raise RuntimeError(
            f"{type(self).__name__} received unexpected message `{msg}`"
        )

    def _is_in_component_tree(self, cache: dict[rio.Component, bool]) -> bool:
        """
        Returns whether this component is directly or indirectly connected to the
        component tree of a session.

        This operation is fast, but has to walk up the component tree to make sure
        the component's parent is also connected. Thus, when checking multiple
        components it can easily happen that the same components are checked over and
        over, resulting on O(n log n) runtime. To avoid this, pass a cache
        dictionary to this function, which will be used to memoize the result.

        Be careful not to reuse the cache if the component hierarchy might have
        changed (for example after an async yield).
        """

        # Already cached?
        try:
            return cache[self]
        except KeyError:
            pass

        # Root component?
        if self is self.session._root_component:
            result = True

        # Has the builder has been garbage collected?
        else:
            builder = self._weak_builder_()
            if builder is None:
                result = False

            # Has the builder since created new build output, and this component
            # isn't part of it anymore?
            else:
                parent_data = self.session._weak_component_data_by_component[
                    builder
                ]
                result = (
                    parent_data.build_generation == self._build_generation_
                    and builder._is_in_component_tree(cache)
                )

        # Cache the result and return
        cache[self] = result
        return result

    @overload
    async def call_event_handler(
        self,
        handler: rio.EventHandler[[]],
    ) -> None: ...  # pragma: no cover

    @overload
    async def call_event_handler(
        self,
        handler: rio.EventHandler[[T]],
        event_data: T,
        /,
    ) -> None: ...  # pragma: no cover

    async def call_event_handler(
        self,
        handler: rio.EventHandler[...],
        *event_data: object,
    ) -> None:
        """
        Calls an even handler, awaiting it if necessary.

        Call an event handler, if one is present. Await it if necessary. Log and
        discard any exceptions. If `event_data` is present, it will be passed to
        the event handler.

        ## Parameters

        `handler`: The event handler (function) to call.

        `event_data`: Arguments to pass to the event handler.
        """
        await self.session._call_event_handler(
            handler, *event_data, refresh=False
        )

    async def force_refresh(self) -> None:
        """
        Force a rebuild of this component.

        Most of the time components update automatically when their state
        changes. However, some state mutations are invisible to `Rio`: For
        example, appending items to a list modifies the list, but since no list
        instance was actually assigned to th component, `Rio` will be unaware of
        this change.

        In these cases, you can force a rebuild of the component by calling
        `force_refresh`. This will trigger a rebuild of the component and
        display the updated version on the screen.

        Another common use case is if you wish to update an component while an
        event handler is still running. `Rio` will automatically detect changes
        after event handlers return, but if you are performing a long-running
        operation, you may wish to update the component while the event handler
        is still running. This allows you to e.g. update a progress bar while
        the operation is still running.
        """
        self.session._register_dirty_component(
            self,
            include_children_recursively=False,
        )

        await self.session._refresh()

    def _get_debug_details(self) -> dict[str, Any]:
        """
        Used by Rio's debugger to decide which properties to display to a user,
        when they select a component.
        """
        result = {}

        for prop in self._state_properties_:
            # Consider properties starting with an underscore internal
            if prop.startswith("_"):
                continue

            # Keep it
            result[prop] = getattr(self, prop)

        return result

    def __repr__(self) -> str:
        result = f"<{type(self).__name__} id:{self._id}"

        child_strings: list[str] = []
        for child in self._iter_direct_children():
            child_strings.append(f" {type(child).__name__}:{child._id}")

        if child_strings:
            result += " -" + "".join(child_strings)

        return result + ">"

    def _repr_tree_worker(self, file: IO[str], indent: str) -> None:
        file.write(indent)
        file.write(repr(self))

        for child in self._iter_direct_children():
            file.write("\n")
            child._repr_tree_worker(file, indent + "    ")

    def _repr_tree(self) -> str:
        file = io.StringIO()
        self._repr_tree_worker(file, "")
        return file.getvalue()
