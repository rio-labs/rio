from __future__ import annotations

import asyncio
import dataclasses
import typing as t
import warnings
import weakref
from collections import defaultdict

import introspection
import typing_extensions as te

import rio

from . import event, global_state, inspection
from .observables.dataclass import RioDataclassMeta, internal_field
from .utils import I_KNOW_WHAT_IM_DOING
from .warnings import RioPotentialMistakeWarning

__all__ = ["ComponentMeta"]


C = t.TypeVar("C", bound="rio.Component")


# For some reason vscode doesn't understand that this class is a
# `@te.dataclass_transform`, so we'll annotate it again...
@te.dataclass_transform(
    eq_default=False,
    field_specifiers=(internal_field, dataclasses.field),
)
class ComponentMeta(RioDataclassMeta):
    # Maps event tags to the methods that handle them. The methods aren't bound
    # to the instance yet, so make sure to pass `self` when calling them
    #
    # The assigned value is needed so that the `Component` class itself has a
    # valid value. All subclasses override this value in `__init_subclass__`.
    _rio_event_handlers_: defaultdict[
        event.EventTag, list[tuple[t.Callable, t.Any]]
    ]

    # Whether this component class is built into Rio, rather than user defined,
    # or from a library.
    _rio_builtin_: bool

    def __init__(cls, *args, **kwargs):
        # Is this class built into Rio?
        cls._rio_builtin_ = cls.__module__.startswith("rio.")

        # Run sanity checks
        if not cls._rio_builtin_:
            try:
                init_func = vars(cls)["__init__"]
            except KeyError:
                pass
            else:
                if init_func not in I_KNOW_WHAT_IM_DOING:
                    warnings.warn(
                        f"`{cls.__name__}` has a custom `__init__` method. This"
                        f" can lead to subtle bugs, so it's usually better to"
                        f" let rio create the constructor automatically. If you"
                        f" need to run code during initialization, use"
                        f" `__post_init__` instead. Otherwise, if you are"
                        f" absolutely sure this is okay, you can silence this"
                        f" warning by adding a `@rio.i_know_what_im_doing`"
                        f" decorator to the `__init__` method.",
                        RioPotentialMistakeWarning,
                    )

        super().__init__(*args, **kwargs)

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
                events = member._rio_events_  # type: ignore
            except AttributeError:
                continue

            for event_tag, args in events.items():
                for arg in args:
                    cls._rio_event_handlers_[event_tag].append((member, arg))

    @introspection.mark.does_not_alter_signature
    def __call__(
        cls: type[C],  # type: ignore
        *args: object,
        **kwargs: object,
    ) -> C:
        # Fetch the session this component is part of
        if global_state.currently_building_session is None:
            raise RuntimeError(
                "Components can only be created inside of `build` methods."
            )

        # Remap deprecated parameter names to new ones
        args, kwargs = cls._remap_constructor_arguments_(args, kwargs)

        component: C = object.__new__(cls)

        # Inject the session before calling the constructor
        session = global_state.currently_building_session
        component._session_ = session

        # Create a unique ID for this component
        component._id_ = session._next_free_component_id
        session._next_free_component_id += 1

        # Register it as a newly created component. This causes it to be built
        # for the first time, which otherwise wouldn't happen since this
        # component doesn't depend on any state yet.
        #
        # Rio also tracks everything that's accessed during `build` functions,
        # so it nows when to rebuild the component. This often includes
        # attributes of newly created components which were somehow accessed
        # indirectly, which is why it's special-cased that a component can't
        # depend on any attributes of child components. It is therefore
        # extremely important that we register this component as newly created,
        # even if we later throw an exception (due to duplicate keys or invalid
        # assignments or whatever).
        session._newly_created_components.add(component)

        component._properties_assigned_after_creation_ = set()

        # Call `__init__`
        component.__init__(*args, **kwargs)
        component._init_called_ = True

        # Some components (like `Grid`) manually mark some properties as
        # explicitly set in their `__init__`, so we must use `.update()` instead
        # of an assignment
        component._properties_set_by_creator_.update(
            inspection.get_explicitly_set_state_property_names(
                component,
                args,
                kwargs,
            )
        )

        # If the component has a `key`, register it
        key = component.key
        if key is not None:
            if key in global_state.key_to_component:
                raise RuntimeError(
                    f'Multiple components share the key "{key}": {global_state.key_to_component[key]} and {component}'
                )

            global_state.key_to_component[key] = component

        # Keep track of this component's existence
        #
        # Components must be known by their id, so any messages addressed to
        # them can be passed on correctly.
        session._weak_components_by_id[component._id_] = component

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

            # Window resizes are handled by the session. Register the handler
            elif event_tag == event.EventTag.ON_WINDOW_SIZE_CHANGE:
                callbacks = tuple(handler for handler, unused in event_handlers)
                session._on_window_size_change_callbacks[component] = callbacks

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


async def _periodic_event_worker(
    weak_component: weakref.ReferenceType[rio.Component],
    handler: t.Callable,
    period: float,
) -> None:
    # Get a handle on the session
    try:
        sess = weak_component().session  # type: ignore
    except AttributeError:
        return

    # Keep running for as long as the component exists
    while True:
        # Wait for the next tick
        await asyncio.sleep(period)

        # Wait until there's an active connection to the client. We won't run
        # code periodically if we aren't sure whether the client will come back.
        await sess._is_connected_event.wait()

        # Does the component still exist?
        component = weak_component()

        if component is None:
            return

        # Call the handler
        await component.call_event_handler(handler, component)
        await sess._refresh()

        # Drop the reference to the component
        component = None
