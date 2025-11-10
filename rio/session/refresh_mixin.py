from __future__ import annotations

import asyncio
import collections
import typing as t
import weakref

import uniserde
from identity_containers import IdentityDefaultDict, IdentitySet

import rio

from .. import (
    weak_key_id_default_dict,
    global_state,
    serialization,
    inspection,
    utils,
)
from ..components import fundamental_component
from ..data_models import BuildData
from ..observables.observable_property import AttributeBinding


class SessionRefreshMixin:
    def __init__(self):
        # Sessions automatically rebuild components whenever necessary. To make
        # this possible, we need to create a background task that waits for a
        # component to become dirty. It can do that by waiting for this event,
        # which is triggered by our observables.
        self._refresh_required_event = asyncio.Event()

        # Map observables to components that accessed them. Whenever an
        # observable's value changes, the corresponding components will be
        # rebuilt.
        self._components_by_accessed_object: weak_key_id_default_dict.WeakKeyIdDefaultDict[
            object, weakref.WeakSet[rio.Component]
        ] = weak_key_id_default_dict.WeakKeyIdDefaultDict(weakref.WeakSet)

        self._components_by_accessed_attr: weak_key_id_default_dict.WeakKeyIdDefaultDict[
            object, collections.defaultdict[str, weakref.WeakSet[rio.Component]]
        ] = weak_key_id_default_dict.WeakKeyIdDefaultDict(
            lambda: collections.defaultdict(weakref.WeakSet)
        )

        self._components_by_accessed_item: weak_key_id_default_dict.WeakKeyIdDefaultDict[
            object,
            collections.defaultdict[object, weakref.WeakSet[rio.Component]],
        ] = weak_key_id_default_dict.WeakKeyIdDefaultDict(
            lambda: collections.defaultdict(weakref.WeakSet)
        )

        # Keep track of all observables that have changed since the last refresh
        self._changed_objects = IdentitySet[object]()
        self._changed_attributes = IdentityDefaultDict[object, set[str]](set)
        self._changed_items = IdentityDefaultDict[object, IdentitySet[object]](
            IdentitySet[object]
        )

        # This lock is used to order state updates that are sent to the client.
        # Without it a message which was generated later might be sent to the
        # client before an earlier message, leading to invalid component
        # references.
        self._refresh_lock = asyncio.Lock()

        # A dict of {build_function: error_message}. This is cleared at
        # the start of every refresh, and tracks which build functions failed.
        # Used for unit testing.
        self._crashed_build_functions = dict[t.Callable, str]()

        # Weak dictionaries to hold additional information about components.
        # These are split in two to avoid the dictionaries keeping the
        # components alive. Notice how both dictionaries are weak on the actual
        # component.
        #
        # Never access these directly. Instead, use helper functions
        # - `lookup_component`
        # - `lookup_component_data`
        self._weak_components_by_id: weakref.WeakValueDictionary[
            int, rio.Component
        ] = weakref.WeakValueDictionary()

        # Stores newly created components. These need to be built/refreshed.
        #
        # This is an identity set to make it safe to look up the presence of any
        # Python object, regardless of whether it is hashable, without any slow
        # prior checks.
        self._newly_created_components = IdentitySet[rio.Component]()

    async def _refresh_whenever_necessary(self) -> None:
        while True:
            await self._refresh_required_event.wait()
            await self._refresh()

    def _dbg_why_dirty(self, component_or_id: rio.Component | int):
        """
        For debugging. Tells you why a component is dirty.
        """
        if isinstance(component_or_id, int):
            component = self._weak_components_by_id[component_or_id]
        else:
            component = component_or_id

        results = list[str]()

        if component in self._newly_created_components:
            results.append("newly created")

        for obj in self._changed_objects:
            if component in self._components_by_accessed_object[obj]:
                results.append(f"object {obj!r} changed")

        for obj, changed_attrs in self._changed_attributes.items():
            if obj is component:
                if isinstance(obj, fundamental_component.FundamentalComponent):
                    results.append(
                        f"its own attributes changed: {changed_attrs}"
                    )

                if not changed_attrs.isdisjoint(rio.Component.__annotations__):
                    results.append(
                        f"its own attributes changed: {changed_attrs}"
                    )

            dependents_by_changed_attr = self._components_by_accessed_attr[obj]

            for changed_attr in changed_attrs:
                if component in dependents_by_changed_attr[changed_attr]:
                    results.append(
                        f"attribute {changed_attr!r} of {obj} changed"
                    )

        for obj, changed_items in self._changed_attributes.items():
            dependents_by_changed_item = self._components_by_accessed_item[obj]

            for changed_item in changed_items:
                if component in dependents_by_changed_item[changed_item]:
                    results.append(f"item {changed_item!r} of {obj} changed")

        return results

    def _collect_components_to_build(self) -> set[rio.Component]:
        # Note: If you're debugging this function, the
        # `Session._dbg_why_dirty(component)` method can help you figure out how
        # a component ends up in `components_to_build`.

        components_to_build = set[rio.Component]()

        # Add newly instantiated components
        components_to_build.update(self._newly_created_components)

        # Add components that depend on observable objects that have changed
        for obj in self._changed_objects:
            components_to_build.update(self._components_by_accessed_object[obj])

        # Add components that depend on properties that have changed
        for obj, changed_attrs in self._changed_attributes.items():
            if not changed_attrs:
                continue

            if isinstance(obj, rio.Component):
                # If the object is a FundamentalComponent, add it too. It doesn't
                # have a `build` method, but it obviously does depend on its own
                # properties.
                if isinstance(obj, fundamental_component.FundamentalComponent):
                    components_to_build.add(obj)

                # Same thing goes for builtin attributes: Things like `min_width`
                # aren't used in the `build` function, but still need to be sent to
                # the frontend.
                if not changed_attrs.isdisjoint(rio.Component.__annotations__):
                    components_to_build.add(obj)

            # Add all components that depend on this attribute
            dependents_by_changed_attr = self._components_by_accessed_attr[obj]

            for changed_attr in changed_attrs:
                components_to_build.update(
                    dependents_by_changed_attr[changed_attr]
                )

        # Add components that depend on items that have changed
        for obj, changed_items in self._changed_items.items():
            if not changed_items:
                continue

            # If the object is a FundamentalComponent, add it too. It doesn't
            # have a `build` method, but it obviously does depend on its own
            # properties.
            if isinstance(obj, fundamental_component.FundamentalComponent):
                components_to_build.add(obj)

            # Add all components that depend on this attribute
            dependents_by_changed_item = self._components_by_accessed_item[obj]

            for changed_item in changed_items:
                components_to_build.update(
                    dependents_by_changed_item[changed_item]
                )

        return components_to_build

    def _build_component(self, component: rio.Component) -> set[rio.Component]:
        return self._build_high_level_component(component)

        if isinstance(component, fundamental_component.FundamentalComponent):
            children = component._iter_tree_children_(
                include_self=False,
                recurse_into_fundamental_components=False,
                recurse_into_high_level_components=False,
            )
        else:
            old_child = component._build_data_.build_result
            self._build_high_level_component(component)
            new_child = component._build_data_.build_result

            children = [new_child]

        component_ref = weakref.ref(component)
        for child in children:
            child._weak_parent_ = component_ref

    def _build_high_level_component(self, component: rio.Component):
        # Trigger the `on_populate` event, if it hasn't already.
        if not component._on_populate_triggered_:
            component._on_populate_triggered_ = True

            for handler, _ in component._rio_event_handlers_[
                rio.event.EventTag.ON_POPULATE
            ]:
                # Since the whole point of this event is to fetch data and
                # modify the component's state, wait for it to finish if it's
                # synchronous.
                self._call_event_handler_sync(handler, component)

            # If the event handler made the component dirty again, undo it
            self._changed_attributes.pop(component, None)

        # Call the `build` method
        global_state.currently_building_component = component
        global_state.currently_building_session = self
        global_state.accessed_objects.clear()
        global_state.accessed_attributes.clear()
        global_state.accessed_items.clear()

        build_result = utils.safe_build(component.build)

        accessed_attrs = [
            (obj, set(attrs))
            for obj, attrs in global_state.accessed_attributes.items()
        ]

        global_state.currently_building_component = None
        global_state.currently_building_session = None

        key_to_component = global_state.key_to_component
        global_state.key_to_component = {}

        # Process the state that was accessed by the `build` method
        for obj in global_state.accessed_objects:
            self._components_by_accessed_object[obj].add(component)

        for obj, accessed_attrs in global_state.accessed_attributes.items():
            # Sometimes a `build` method indirectly accesses the state of a
            # child component. For example, calling `Row.add()` "accesses"
            # `Row.children`. This can lead to an infinite loop: Because the
            # child was freshly instantiated, all of its attributes have
            # "changed", thus rebuilding the parent, thus rebuilding the child,
            # etc.
            #
            # Workaround: Parents can't depend on the properties of their
            # children.
            if obj in self._newly_created_components:
                continue

            components_by_accessed_attr = self._components_by_accessed_attr[obj]

            for accessed_attr in accessed_attrs:
                components_by_accessed_attr[accessed_attr].add(component)

        for obj, accessed_items in global_state.accessed_items.items():
            components_by_accessed_item = self._components_by_accessed_item[obj]

            for accessed_item in accessed_items:
                components_by_accessed_item[accessed_item].add(component)

        if component in self._changed_attributes:
            raise RuntimeError(
                f"The `build()` method of the component `{component}`"
                f" has changed the component's state. This isn't"
                f" supported, because it would trigger an immediate"
                f" rebuild, and thus result in an infinite loop. Make"
                f" sure to perform any changes outside of the `build`"
                f" function, e.g. in event handlers."
            )

        # Has this component been built before?
        component_data = component._build_data_

        # No, this is the first time
        if component_data is None:
            # Create the component data and cache it
            component_data = component._build_data_ = BuildData(
                build_result,
                set(),  # Set of all children - filled in below
                key_to_component,
            )

        # Yes, rescue state. This will:
        #
        # - Look for components in the build output which correspond to
        #   components in the previous build output, and transfers state
        #   from the new to the old component ("reconciliation")
        #
        # - Replace any references to new, reconciled components in the
        #   build output with the old components instead
        #
        # - Add any dirty components from the build output (new, or old
        #   but changed) to the dirty set.
        #
        # - Update the component data with the build output resulting
        #   from the operations above
        else:
            self._reconcile_tree(component_data, build_result, key_to_component)

            # Reconciliation can change the build result. Make sure
            # nobody uses `build_result` instead of
            # `component_data.build_result` from now on.
            del build_result

        # Remember the previous children of this component
        old_children_in_build_boundary = (
            component_data.all_children_in_build_boundary
        )

        # Inject the builder and build generation
        weak_builder = weakref.ref(component)

        if isinstance(
            component_data.build_result,
            fundamental_component.FundamentalComponent,
        ):
            component_data.all_children_in_build_boundary = set(
                component_data.build_result._iter_tree_children_(
                    include_self=True,
                    recurse_into_fundamental_components=True,
                    recurse_into_high_level_components=False,
                )
            )
        else:
            component_data.all_children_in_build_boundary = {
                component_data.build_result
            }

        for child in component_data.all_children_in_build_boundary:
            child._weak_parent_ = weak_builder

        return old_children_in_build_boundary

    def _refresh_sync(
        self,
    ) -> tuple[
        dict[rio.Component, set[str]],
        t.Iterable[rio.Component],
        t.Iterable[rio.Component],
    ]:
        """
        See `refresh` for details on what this function does.

        The refresh process must be performed atomically, without ever yielding
        control flow to the async event loop. TODO WHY

        To make sure async isn't used unintentionally this part of the refresh
        function is split into a separate, synchronous function.

        The session keeps track of components which are no longer referenced in
        its component tree. Those components are NOT included in the function's
        result.
        """

        # Keep track of all components which are visited. These have changed
        # somehow and thus must be sent to the client.
        visited_components: collections.Counter[rio.Component] = (
            collections.Counter()
        )

        # Keep track of all changed properties for each component. The
        # serializer will need this information later
        component_properties_to_serialize = collections.defaultdict[
            rio.Component, set[str]
        ](set)

        # Keep track of of previous child components
        old_children_in_build_boundary_for_visited_children = dict[
            rio.Component, set[rio.Component]
        ]()

        # Build all dirty components
        for component in self._collect_all_components_to_build(
            component_properties_to_serialize
        ):
            # Remember that this component has been visited
            visited_components[component] += 1

            # Catch deep recursions and abort
            build_count = visited_components[component]
            if build_count >= 5:
                raise RecursionError(
                    f"The component `{component}` has been rebuilt"
                    f" {build_count} times during a single refresh. This is"
                    f" likely because one of your components' `build`"
                    f" methods is modifying the component's state"
                )

            # Fundamental components require no further treatment
            if isinstance(
                component, fundamental_component.FundamentalComponent
            ):
                continue

            # Others need to be built
            old_children_in_build_boundary_for_visited_children[component] = (
                self._build_component(component)
            )

            component._needs_rebuild_on_mount_ = False

            # There is a possibility that a component's build data isn't
            # up to date because it wasn't in the tree when the last build
            # was scheduled. Find such components and queue them for a
            # build.
            assert component._build_data_ is not None

            for comp in component._build_data_.all_children_in_build_boundary:
                if comp._needs_rebuild_on_mount_:
                    raise NotImplementedError  # FIXME
                    components_to_build.add(comp)

        # Determine which components are alive, to avoid sending references
        # to dead components to the frontend.
        is_in_component_tree_cache: dict[rio.Component, bool] = {
            self._high_level_root_component: True,
        }

        visited_and_live_components: set[rio.Component] = {
            component
            for component in visited_components
            if component._is_in_component_tree_(is_in_component_tree_cache)
        }

        all_children_old = set[rio.Component]()
        all_children_new = set[rio.Component]()

        for component in visited_components:
            # We only look at high level components, since we already have a set
            # of all children in the build boundary
            if isinstance(
                component, fundamental_component.FundamentalComponent
            ):
                continue

            all_children_old.update(
                c
                for comp in old_children_in_build_boundary_for_visited_children[
                    component
                ]
                for c in comp._iter_tree_children_(
                    include_self=True,
                    recurse_into_fundamental_components=True,
                    recurse_into_high_level_components=True,
                )
            )
            all_children_new.update(
                c
                for comp in component._build_data_.all_children_in_build_boundary  # type: ignore
                for c in comp._iter_tree_children_(
                    include_self=True,
                    recurse_into_fundamental_components=True,
                    recurse_into_high_level_components=True,
                )
            )

        # Find out which components were mounted or unmounted
        mounted_components = all_children_new - all_children_old
        unmounted_components = all_children_old - all_children_new

        # The state/children of newly mounted components must also be sent to
        # the client.
        unvisited_mounted_components = (
            mounted_components - visited_and_live_components
        )

        for component in unvisited_mounted_components:
            recursive_children = component._iter_tree_children_(
                include_self=True,
                recurse_into_fundamental_components=True,
                recurse_into_high_level_components=True,
            )
            visited_and_live_components.update(recursive_children)

        # Make sure *all* properties of mounted components are sent to the
        # frontend
        for component in mounted_components:
            component_properties_to_serialize[component] = set(
                serialization.get_all_serializable_property_names(
                    type(component)
                )
            )

        return (
            {
                component: component_properties_to_serialize[component]
                for component in visited_and_live_components
            },
            mounted_components,
            unmounted_components,
        )

    def _collect_all_components_to_build(
        self,
        properties_to_serialize: collections.defaultdict[
            rio.Component, set[str]
        ],
    ):
        components_to_build = set[rio.Component]()

        while True:
            # Update the properties_to_serialize
            for obj, changed_properties in self._changed_attributes.items():
                properties_to_serialize[obj].update(changed_properties)

            # Collect all dirty components
            components_to_build.update(self._collect_components_to_build())
            self._newly_created_components.clear()
            self._changed_objects.clear()
            self._changed_attributes.clear()
            self._changed_items.clear()
            self._refresh_required_event.clear()

            # We need to build parents before children, but some components
            # haven't had their `_weak_parent_` set yet, so we don't know who
            # their parent is. We need to find the topmost components and build
            # them.

            # TODO: This is not entirely correct, because during the build
            # process, new components can be instantiated or the level of an
            # existing component can change. The correct solution would be to
            # process one component, then call `_collect_components_to_build()`
            # again, and sort again.
            component_level = dict[rio.Component, int]()
            component_level[self._high_level_root_component] = 0

            def determine_component_level(component: rio.Component) -> int:
                parent = component._weak_parent_()
                if parent is not None:
                    return get_component_level(parent) + 1

                if isinstance(
                    component,
                    rio.components.dialog_container.DialogContainer,
                ):
                    try:
                        owning_component = self._weak_components_by_id[
                            component.owning_component_id
                        ]
                    except KeyError:
                        return -99999

                    if component._id_ in owning_component._owned_dialogs_:
                        return get_component_level(owning_component) + 1

                    return -99999

                return -99999

            def get_component_level(component: rio.Component) -> int:
                try:
                    return component_level[component]
                except KeyError:
                    level = determine_component_level(component)

                    component_level[component] = level
                    return level

            components_to_build_in_this_iteration = sorted(
                [
                    component
                    for component in components_to_build
                    if get_component_level(component) >= 0
                ],
                key=get_component_level,
            )
            components_to_build.difference_update(
                components_to_build_in_this_iteration
            )

            # If we can't determine the level of even a single component, that
            # means all the remaining components must be dead. (We have already
            # built all "parent" components, so if a component still doesn't
            # have a parent, it must be dead.)
            if not components_to_build_in_this_iteration:
                # Any components which wanted to build but were skipped due to
                # not being part of the component tree need to be tracked, such
                # that they will be rebuilt the next time they are mounted
                # despite not being dirty.
                for component in components_to_build:
                    component._needs_rebuild_on_mount_ = True

                break

            # Don't even build dead components, since their build function might
            # crash
            is_in_component_tree_cache = {
                self._high_level_root_component: True,
            }

            for component in components_to_build_in_this_iteration:
                # If the component is dead, skip it
                if component._is_in_component_tree_(is_in_component_tree_cache):
                    yield component

    async def _refresh(self) -> None:
        """
        Make sure the session state is up to date. Specifically:

        - Call `build` on all dirty components
        - Recursively do this for all freshly spawned components
        - mark all components as clean

        Afterwards, the client is also informed of any changes, meaning that
        after this method returns there are no more dirty components in the
        session, and Python's state and the client's state are in sync.
        """

        # For why this lock is here see its creation in `__init__`
        async with self._refresh_lock:
            # Clear the dict of crashed build functions
            self._crashed_build_functions.clear()

            while True:
                # Refresh and get a set of all components which have been
                # visited
                (
                    component_properties_to_serialize,
                    mounted_components,
                    unmounted_components,
                ) = self._refresh_sync()

                # Avoid sending empty messages
                if not component_properties_to_serialize:
                    return

                # Serialize all components which need to be sent to the client
                await self._update_component_states(
                    component_properties_to_serialize
                )

                # Trigger the `on_unmount` event
                #
                # Notes:
                # - All events are triggered only after the client has been
                #   notified of the changes. This way, if the event handlers
                #   trigger another client message themselves, any referenced
                #   components will already exist
                for component in unmounted_components:
                    # Trigger the event
                    for handler, _ in component._rio_event_handlers_[
                        rio.event.EventTag.ON_UNMOUNT
                    ]:
                        self._call_event_handler_sync(handler, component)

                # Trigger the `on_mount` event
                #
                # Notes:
                # - See the note on running after notifying the client above
                # - This function enlarges the set of watched components. The
                #   `on_unmount` event handler iterates over that set. By
                #   processing that handler first it only needs to process a
                #   smaller set
                for component in mounted_components:
                    # Trigger the event
                    for handler, _ in component._rio_event_handlers_[
                        rio.event.EventTag.ON_MOUNT
                    ]:
                        self._call_event_handler_sync(handler, component)

                # If there were any synchronous `on_mount` or `on_unmount`
                # handlers, we must immediately refresh again. So we'll simply
                # loop until there are no more dirty components.

    async def _update_component_states(
        self,
        component_properties_to_send: t.Mapping[rio.Component, t.Iterable[str]],
    ) -> None:
        # Initialize all new FundamentalComponents
        tasks = list[asyncio.Task]()

        for component in component_properties_to_send:
            if (
                not isinstance(
                    component, fundamental_component.FundamentalComponent
                )
                or component._unique_id_ in self._initialized_html_components
            ):
                continue

            task = self.create_task(component._initialize_on_client(self))
            tasks.append(task)

            self._initialized_html_components.add(component._unique_id_)

        for task in tasks:
            await task

        # Serialize the component states
        delta_states: dict[int, uniserde.JsonDoc] = {
            component._id_: serialization.serialize_and_host_component(
                component, props
            )
            for component, props in component_properties_to_send.items()
        }

        # Check whether the root component needs replacing. Take care to never
        # send the high level root component. JS only cares about the
        # fundamental one.
        if self._high_level_root_component in component_properties_to_send:
            del delta_states[self._high_level_root_component._id_]

            root_build: BuildData = self._high_level_root_component._build_data_  # type: ignore
            fundamental_root_component = root_build.build_result
            assert isinstance(
                fundamental_root_component,
                fundamental_component.FundamentalComponent,
            ), fundamental_root_component
            root_component_id = fundamental_root_component._id_
        else:
            root_component_id = None

        # Send the new state to the client
        await self._remote_update_component_states(
            delta_states,
            root_component_id,
        )

    async def _send_all_components_on_reconnect(self) -> None:
        self._initialized_html_components.clear()

        # For why this lock is here see its creation in `__init__`
        async with self._refresh_lock:
            all_components = (
                self._high_level_root_component._iter_tree_children_(
                    include_self=True,
                    recurse_into_fundamental_components=True,
                    recurse_into_high_level_components=True,
                )
            )
            properties_to_send = {
                component: serialization.get_all_serializable_property_names(
                    type(component)
                )
                for component in all_components
            }

            await self._update_component_states(properties_to_send)

    def _reconcile_tree(
        self,
        old_build_data: BuildData,
        new_build: rio.Component,
        new_key_to_component: dict[rio.components.component.Key, rio.Component],
    ) -> None:
        # Find all pairs of components which should be reconciled
        matched_pairs = self._find_components_for_reconciliation(
            old_build_data.build_result,
            new_build,
            old_build_data.key_to_component,
            new_key_to_component,
        )

        # Reconciliating individual components requires knowledge of which other
        # components are being reconciled.
        #
        # -> Collect them into a dict first.
        reconciled_components_new_to_old: dict[rio.Component, rio.Component] = {
            new_component: old_component
            for old_component, new_component in matched_pairs
        }

        # Update the key to component mapping. Take the keys from the new dict,
        # but replace the components with the reconciled ones.
        old_build_data.key_to_component = {
            key: reconciled_components_new_to_old.get(component, component)
            for key, component in new_key_to_component.items()
        }

        # For FundamentalComponents, keep track of children that were added or
        # removed. Removed children must also be removed from their builder's
        # `all_children_in_build_boundary` set. (See
        # `test_reconcile_not_dirty_high_level_component` for more details.)
        added_children_by_builder = collections.defaultdict[
            rio.Component, set[rio.Component]
        ](set)
        removed_children_by_builder = collections.defaultdict[
            rio.Component, set[rio.Component]
        ](set)

        # Reconcile all matched pairs
        for (
            new_component,
            old_component,
        ) in reconciled_components_new_to_old.items():
            assert new_component is not old_component, (
                f"Attempted to reconcile {new_component!r} with itself!?"
            )

            added_children, removed_children = self._reconcile_component(
                old_component,
                new_component,
                reconciled_components_new_to_old,
            )

            builder = old_component._weak_parent_()
            if builder is not None:
                added_children_by_builder[builder].update(added_children)
                removed_children_by_builder[builder].update(removed_children)

            # Avoid building the new components. This is not just a performance
            # optimization.
            #
            # When building, components assign themselves as weak builder to all
            # of their build output. If these components were allowed to build
            # themselves, they'd override the actual weak builder with
            # themselves.
            self._newly_created_components.discard(new_component)
            self._changed_attributes.pop(new_component, None)

        # Now that we have collected all added and removed children, update the
        # builder's `all_children_in_build_boundary` set
        for builder, added_children in added_children_by_builder.items():
            build_data = builder._build_data_
            if build_data is None:
                continue

            # build_data.all_children_in_build_boundary.difference_update(
            #     removed_children_by_builder[builder]
            # )
            # build_data.all_children_in_build_boundary.update(
            #     reconciled_components_new_to_old.get(new_child, new_child)
            #     for new_child in added_children
            # )

        # Update the component data. If the root component was not reconciled,
        # the new component is the new build result.
        try:
            reconciled_build_result = reconciled_components_new_to_old[
                new_build
            ]
        except KeyError:
            reconciled_build_result = new_build
            old_build_data.build_result = new_build

        def ensure_weak_builder_is_set(
            parent: rio.Component, child: rio.Component
        ) -> None:
            """
            This function makes sure that any components which are now in the
            tree have their builder properly set.

            The problem is that the `_weak_builder_` is only set after a high
            level component is built, but there are situations where a
            FundamentalComponent received a new child and its parent high level
            component is not dirty.

            For more details, see
            `test_reconcile_not_dirty_high_level_component`.
            """
            if not isinstance(
                parent, fundamental_component.FundamentalComponent
            ):
                return

            builder = parent._weak_parent_()

            # It's possible that the builder has not been initialized yet. The
            # builder is only set for children inside of a high level
            # component's build boundary, but `remap_components` crosses build
            # boundaries. So if the builder is not set, we simply do nothing -
            # it will be set later, once our high level parent component is
            # built.
            if builder is None:
                return  # TODO: WRITE A UNIT TEST FOR THIS

            child._weak_parent_ = parent._weak_parent_

            # build_data = builder._build_data_
            # if build_data is not None:
            #     build_data.all_children_in_build_boundary.add(child)

        # Replace any references to new reconciled components to old ones instead
        def remap_components(parent: rio.Component) -> None:
            parent_vars = vars(parent)

            for (
                attr_name
            ) in inspection.get_child_component_containing_attribute_names(
                type(parent)
            ):
                attr_value = parent_vars[attr_name]

                # Just a component
                if isinstance(attr_value, rio.Component):
                    try:
                        attr_value = reconciled_components_new_to_old[
                            attr_value
                        ]
                    except KeyError:
                        ensure_weak_builder_is_set(parent, attr_value)
                    else:
                        parent_vars[attr_name] = attr_value

                    remap_components(attr_value)

                # List / Collection
                else:
                    try:
                        iterator = iter(attr_value)
                    except TypeError:
                        continue

                    for ii, item in enumerate(iterator):
                        if isinstance(item, rio.Component):
                            try:
                                item = reconciled_components_new_to_old[item]
                            except KeyError:
                                ensure_weak_builder_is_set(parent, item)
                            else:
                                attr_value[ii] = item

                            remap_components(item)

        remap_components(reconciled_build_result)

    def _reconcile_component(
        self,
        old_component: rio.Component,
        new_component: rio.Component,
        reconciled_components_new_to_old: dict[rio.Component, rio.Component],
    ) -> tuple[set[rio.Component], set[rio.Component]]:
        """
        Given two components of the same type, reconcile them. Specifically:

        - Any state which was explicitly set by the user in the new component's
          constructor is considered explicitly set, and will be copied into the
          old component
        - If any values were changed, the component is registered as dirty with
          the session

        This function also handles `StateBinding`s, for details see comments.
        """
        assert type(old_component) is type(new_component), (
            old_component,
            new_component,
        )
        assert old_component.key == new_component.key, (
            old_component.key,
            new_component.key,
        )
        assert old_component is not new_component

        # Determine which properties will be taken from the new component
        overridden_values: dict[str, object] = {}
        old_component_dict = vars(old_component)
        new_component_dict = vars(new_component)

        overridden_property_names = (
            old_component._properties_set_by_creator_
            - old_component._properties_assigned_after_creation_
        ) | new_component._properties_set_by_creator_

        for prop_name in overridden_property_names:
            # Take care to keep attribute bindings up to date
            old_value = old_component_dict[prop_name]
            new_value = new_component_dict[prop_name]
            old_is_binding = isinstance(old_value, AttributeBinding)
            new_is_binding = isinstance(new_value, AttributeBinding)

            # If the old value was a binding, and the new one isn't, split the
            # tree of bindings. All children are now roots.
            if old_is_binding and not new_is_binding:
                binding_value = old_value.get_value()
                old_value.owning_instance_weak = lambda: None

                for child_binding in old_value.children:
                    child_binding.parent = None
                    child_binding.value = binding_value

            # If both values are bindings transfer the children to the new
            # binding
            elif old_is_binding and new_is_binding:
                new_value.owning_instance_weak = old_value.owning_instance_weak
                new_value.children = old_value.children

                for child in old_value.children:
                    child.parent = new_value

                # Save the binding's value in case this is the root binding
                new_value.value = old_value.value

            overridden_values[prop_name] = new_value

        # Keep track of added and removed child components
        added_children = set[rio.Component]()
        removed_children = set[rio.Component]()
        if isinstance(
            old_component, fundamental_component.FundamentalComponent
        ):
            child_containing_attributes = (
                inspection.get_child_component_containing_attribute_names(
                    type(old_component)
                )
            )

            for attr_name in child_containing_attributes:
                removed_children.update(
                    extract_child_components(old_component, attr_name)
                )
                added_children.update(
                    extract_child_components(new_component, attr_name)
                )

        # If the component has changed, mark it as dirty
        def values_equal(old: object, new: object) -> bool:
            """
            Used to compare the old and new values of a property. Returns `True`
            if the values are considered equal, `False` otherwise.
            """
            # Components are a special case. Component attributes are dirty iff
            # the component isn't reconciled, i.e. it is a new component
            if isinstance(new, rio.Component):
                if old is new:
                    return True

                try:
                    new_before_reconciliation = (
                        reconciled_components_new_to_old[new]
                    )
                except KeyError:
                    return False
                else:
                    return old is new_before_reconciliation

            # Lists are compared element-wise
            if isinstance(new, list):
                if not isinstance(old, list):
                    return False

                old = t.cast(list[object], old)
                new = t.cast(list[object], new)

                if len(old) != len(new):
                    return False

                for old_item, new_item in zip(old, new):
                    if not values_equal(old_item, new_item):
                        return False

                return True

            # Otherwise attempt to compare the values
            try:
                return bool(old == new)
            except Exception:
                return old is new

        # Determine which properties have changed
        changed_properties = set[str]()

        for prop_name in overridden_values:
            old_value = getattr(old_component, prop_name)
            new_value = getattr(new_component, prop_name)

            if not values_equal(old_value, new_value):
                changed_properties.add(prop_name)

        self._changed_attributes[old_component].update(changed_properties)

        # Now combine the old and new dictionaries
        #
        # Notice that the component's `_weak_builder_` is always preserved. So
        # even components whose position in the tree has changed still have the
        # correct builder set.
        old_component_dict.update(overridden_values)

        # Update the metadata
        old_component._properties_set_by_creator_ = (
            new_component._properties_set_by_creator_
        )

        # If the component has a `on_populate` handler, it must be triggered
        # again
        old_component._on_populate_triggered_ = False

        return added_children, removed_children

    def _find_components_for_reconciliation(
        self,
        old_build: rio.Component,
        new_build: rio.Component,
        old_key_to_component: dict[rio.components.component.Key, rio.Component],
        new_key_to_component: dict[rio.components.component.Key, rio.Component],
    ) -> t.Iterable[tuple[rio.Component, rio.Component]]:
        """
        Given two component trees, find pairs of components which can be
        reconciled, i.e. which represent the "same" component. When exactly
        components are considered to be the same is up to the implementation and
        best-effort.

        Returns an iterable over (old_component, new_component) pairs.
        """

        def can_pair_up(
            old_component: rio.Component, new_component: rio.Component
        ) -> bool:
            # Components of different type are never a pair
            if type(old_component) is not type(new_component):
                return False

            # Components with different keys are never a pair
            if old_component.key != new_component.key:
                return False

            # Don't reconcile a component with itself, it won't end well
            if old_component is new_component:
                return False

            return True

        # Maintain a queue of (old_component, new_component) pairs that MAY
        # represent the same component. If they match, they will be yielded as
        # results, and their children will also be compared with each other.
        queue: list[tuple[rio.Component, rio.Component]] = [
            (old_build, new_build)
        ]

        # Add the components that have keys. Simply throw all potential pairs
        # into the queue.
        for old_key, old_component in old_key_to_component.items():
            try:
                new_component = new_key_to_component[old_key]
            except KeyError:
                continue

            queue.append((old_component, new_component))

        # Process the queue one by one.
        while queue:
            old_component, new_component = queue.pop(0)

            if not can_pair_up(old_component, new_component):
                continue

            yield old_component, new_component

            # Compare the children, but make sure to preserve the topology.
            # Can't just use `iter_direct_children` here, since that would
            # discard topological information.
            for (
                attr_name
            ) in inspection.get_child_component_containing_attribute_names(
                type(old_component)
            ):
                old_children = extract_child_components(
                    old_component, attr_name
                )
                new_children = extract_child_components(
                    new_component, attr_name
                )

                queue.extend(zip(old_children, new_children))


def extract_child_components(
    component: rio.Component,
    attr_name: str,
) -> list[rio.Component]:
    attr = getattr(component, attr_name, None)

    if isinstance(attr, rio.Component):
        return [attr]

    try:
        iterator = iter(attr)  # type: ignore
    except TypeError:
        pass
    else:
        return [item for item in iterator if isinstance(item, rio.Component)]

    return []
