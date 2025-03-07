from __future__ import annotations

import abc
import dataclasses
import io
import typing as t
from pathlib import Path

import typing_extensions as te
from uniserde import Jsonable, JsonDoc

import rio

from .. import deprecations, inspection, utils
from ..component_meta import ComponentMeta
from ..data_models import BuildData
from ..dataclass import internal_field
from ..state_properties import AttributeBindingMaker

__all__ = ["Component"]


T = t.TypeVar("T")
Key = str | int


# Using `metaclass=ComponentMeta` makes this an abstract class, but since
# pyright is too stupid to understand that, we have to additionally inherit from
# `abc.ABC`
class Component(abc.ABC, metaclass=ComponentMeta):
    """
    Base class for all Rio components.

    Components are the building blocks of all Rio apps. Rio already ships with
    many useful components out of the box, but you can also subclass
    `rio.Component` to create your own.

    Components all follow the same basic structure.

    - Class Header
    - Attribute (with type annotations!)
    - custom functions and event handlers
    - `build` method

    Here's a basic example

    ```python
    class HelloComponent(rio.Component):
        # List all of the components attributes here
        name: str

        # Define the build function. It is called when the component is created
        # or any of its attributes have changed
        def build(self) -> rio.Component:
            return rio.Text(f"Hello, {self.name}!")
    ```

    Notice that there is no `__init__` method. That's because all Rio components
    are automatically dataclasses. This means that you can just list the
    attributes of your component as class variables, and Rio will automatically
    create a constructor for you.

    In fact, **never write an `__init__` method for a Rio component** unless you
    know what you're doing. If you do need custom code to run during
    construction, **use the `__post_init__` method** instead. Here's another
    example, with a custom `__post_init__` method:

    ```python
    class HelloComponent(rio.Component):
        name: str
        greeting: str = ""

        # In order to run custom code during initialization, create a
        # `__post_init__` method. This method is called after all internal
        # setup is done, so you are free to access your finished component.
        def __post_init__(self) -> None:
            # If the caller hasn't provided a greeting, we'll make one up
            # based on the connected user's language
            if self.greeting:
                return

            if self.session.preferred_languages[0].startswith("de"):
                self.greeting = "Hallo"
            elif self.session.preferred_languages[0].startswith("es"):
                self.greeting = "Hola"
            elif self.session.preferred_languages[0].startswith("fr"):
                self.greeting = "Bonjour"
            else:
                self.greeting = "Hello"

        def build(self) -> rio.Component:
            return rio.Text(f"{self.greeting}, {self.name}!")
    ```

    This example initializes allows the user to provide a custom greeting, but
    if they don't, it will automatically choose a greeting based on the user's
    language. This needs custom code to run during initialization, so we use
    `__post_init__`.


    ## Attributes

    `key`: A unique identifier for this component. If two components with the
        same key are present during reconciliation they will be considered
        the same component and their state will be preserved. If no key is
        specified, reconciliation falls back to a less precise method, by
        comparing the location of the component in the component tree.

    `margin`: The margin around this component. This is a shorthand for
        setting `margin_left`, `margin_top`, `margin_right` and `margin_bottom`
        to the same value. If multiple conflicting margins are specified the
        most specific one wins. If for example `margin` and `margin_left` are
        both specified, `margin_left` is used for the left side, while the other
        sides use `margin`. Sizes are measured in "font heights", so a margin of
        1 is the height of a single line of text.

    `margin_x`: The horizontal margin around this component. This is a
        shorthand for setting `margin_left` and `margin_right` to the same
        value. If multiple conflicting margins are specified the most
        specific one wins. If for example `margin_x` and `margin_left` are
        both specified, `margin_left` is used for the left side, while the
        other side uses `margin_x`. Sizes are measured in "font heights", so a
        margin of 1 is the height of a single line of text.

    `margin_y`: The vertical margin around this component. This is a shorthand
        for setting `margin_top` and `margin_bottom` to the same value. If
        multiple conflicting margins are specified the most specific one
        wins. If for example `margin_y` and `margin_top` are both specified,
        `margin_top` is used for the top side, while the other side uses
        `margin_y`. Sizes are measured in "font heights", so a margin of 1 is
        the height of a single line of text.

    `margin_left`: The left margin around this component. If multiple
        conflicting margins are specified this one will be used, since it's
        the most specific. If for example `margin_left` and `margin` are
        both specified, `margin_left` is used for the left side, while the
        other sides use `margin`. Sizes are measured in "font heights", so a
        margin of 1 is the height of a single line of text.

    `margin_top`: The top margin around this component. If multiple
        conflicting margins are specified this one will be used, since it's
        the most specific. If for example `margin_top` and `margin` are both
        specified, `margin_top` is used for the top side, while the other
        sides use `margin`. Sizes are measured in "font heights", so a margin
        of 1 is the height of a single line of text.

    `margin_right`: The right margin around this component. If multiple
        conflicting margins are specified this one will be used, since it's
        the most specific. If for example `margin_right` and `margin` are
        both specified, `margin_right` is used for the right side, while the
        other sides use `margin`. Sizes are measured in "font heights", so a
        margin of 1 is the height of a single line of text.

    `margin_bottom`: The bottom margin around this component. If multiple
        conflicting margins are specified this one will be used, since it's
        the most specific. If for example `margin_bottom` and `margin` are
        both specified, `margin_bottom` is used for the bottom side, while
        the other sides use `margin`. Sizes are measured in "font heights", so
        a margin of 1 is the height of a single line of text.

    `min_width`: The minimum amount of horizontal space this component should
        request during layouting. The component will never be smaller than this
        size.

        Please note that the space a `Component` receives during layouting may
        not match the request. As a general rule, for example, containers try to
        pass on all available space to children. If you really want a
        `Component` to only take up as much space as requested, consider
        specifying an alignment.

        Sizes are measured in "font heights", so a width of 1 is the same as the
        height of a single line of text.

    `min_height`: The minimum amount of vertical space this component should
        request during layouting. The component will never be smaller than this
        size.

        Please note that the space a `Component` receives during layouting may
        not match the request. As a general rule, for example, containers try to
        pass on all available space to children. If you really want a
        `Component` to only take up as much space as requested, consider
        specifying an alignment.

        Sizes are measured in "font heights", so a width of 1 is the same as the
        height of a single line of text.

    `grow_x`: Whether this component should request all the superfluous
        horizontal space available in its parent. Containers normally divide up
        any extra space evenly between their children. However, if components
        have `grow_x`, some containers (such as `rio.Row`) will
        give all remaining space to those components first.

    `grow_y`: Whether this component should request all the superfluous
        vertical space available in its parent. Containers normally divide up
        any extra space evenly between their children. However, if components
        have `grow_y`, some containers (such as `rio.Column`) will
        give all remaining space to those components first.

    `align_x`: How this component should be aligned horizontally, if it
        receives more space than it requested. This can be a number between 0
        and 1, where 0 means left-aligned, 0.5 means centered, and 1 means
        right-aligned.

    `align_y`: How this component should be aligned vertically, if it receives
        more space than it requested. This can be a number between 0 and 1,
        where 0 means top-aligned, 0.5 means centered, and 1 means
        bottom-aligned.
    """

    _: dataclasses.KW_ONLY

    # Unfortunately we have to inline the `Key` type here because dataclasses
    # will create constructor signatures where `Key` can't be resolved.
    key: str | int | None = internal_field(default=None, init=True)

    min_width: float = 0
    min_height: float = 0

    # MAX-SIZE-BRANCH max_width: float | None = None
    # MAX-SIZE-BRANCH max_height: float | None = None

    grow_x: bool = False
    grow_y: bool = False

    align_x: float | None = None
    align_y: float | None = None

    # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never"
    # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never"

    margin_left: float | None = None
    margin_top: float | None = None
    margin_right: float | None = None
    margin_bottom: float | None = None

    margin_x: float | None = None
    margin_y: float | None = None
    margin: float | None = None

    _id_: int = internal_field(init=False)

    # Weak reference to the component's builder. Used to check if the component
    # is still part of the component tree.
    #
    # Dataclasses like to turn this function into a method. Make sure it works
    # both with and without `self`.
    #
    # Important: It's tempting to set the default value to a function that
    # throws an error, but that unfortunately doesn't work. Components that
    # don't survive the reconciler never get a reference to their builder, but
    # it's still possible for them to end up in `Session._dirty_components`,
    # which means there will be a check whether the component is still part of
    # the component tree. That is why we must initialize this with a function
    # that returns `None`.
    _weak_builder_: t.Callable[[], Component | None] = internal_field(
        default=lambda *_: None,
        init=False,
    )

    # Note: The BuildData used to be stored in a WeakKeyDictionary in the
    # Session, but because WeakKeyDictionaries hold *strong* references to their
    # values, this led to reference cycles that the garbage collector never
    # cleaned up. The GC essentially saw this:
    #
    # session -> WeakKeyDictionary -> build data -> child component -> parent component
    #
    # Which, notably, doesn't contain a cycle. Storing the BuildData as an
    # attribute solves this problem, because now the GC can see the cycle:
    #
    # parent component -> build data -> child component -> parent component
    _build_data_: BuildData | None = internal_field(default=None, init=False)

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

    # The stackframe which has created this component. Used by the dev tools.
    # Only initialized if in debugging mode.
    _creator_stackframe_: tuple[Path, int] = internal_field(init=False)

    # Whether this component's `__init__` has already been called. Used to
    # verify that the `__init__` doesn't try to read any state properties.
    _init_called_: bool = internal_field(init=False, default=False)

    # Any dialogs which are owned by this component. This keeps them alive until
    # the component is destroyed. The key is the id of the dialog's root
    # component.
    _owned_dialogs_: dict[int, rio.Dialog] = internal_field(
        default_factory=dict, init=False
    )

    # Hide this function from type checkers so they don't think that we accept
    # arbitrary args
    if not t.TYPE_CHECKING:
        # Make sure users don't inherit from rio components. Inheriting from
        # their own components is fine, though.
        def __init_subclass__(cls, *args, **kwargs):
            super().__init_subclass__(*args, **kwargs)

            if cls.__module__.startswith("rio."):
                return

            for base_cls in cls.__bases__:
                if (
                    base_cls is not __class__
                    and base_cls.__name__ != "FundamentalComponent"
                    and issubclass(base_cls, __class__)
                    and base_cls.__module__.startswith("rio.")
                ):
                    raise Exception(
                        "Inheriting from builtin rio components is not supported."
                    )

    @staticmethod
    def _remap_constructor_arguments_(args: tuple, kwargs: dict):
        width: float | t.Literal["grow", "natural"] | None = kwargs.pop(
            "width", None
        )

        if width is None:
            pass
        else:
            deprecations.warn(
                since="0.10",
                message="The `width` attribute of `rio.Component` has been removed. Please use `min_width` and `grow_x` instead.",
            )

            if width == "natural":
                pass
            elif width == "grow":
                kwargs["grow_x"] = True
            else:
                kwargs["min_width"] = width

        height: float | t.Literal["grow", "natural"] | None = kwargs.pop(
            "height", None
        )

        if height is None:
            pass
        else:
            deprecations.warn(
                since="0.10",
                message="The `height` attribute of `rio.Component` has been removed. Please use `min_height` and `grow_y` instead.",
            )

            if height == "natural":
                pass
            elif height == "grow":
                kwargs["grow_y"] = True
            else:
                kwargs["min_height"] = height

        return args, kwargs

    @property
    def session(self) -> rio.Session:
        """
        Return the session this component is part of.

        When a component is created, Rio associates it with the session it was
        built inside of. This is a property that retrieves that session.
        """
        return self._session_

    # There isn't really a good type annotation for this... `te.Self` is the
    # closest thing
    def bind(self) -> te.Self:
        """
        Create an attribute binding between this component and one of its
        children.

        Attribute bindings allow a child component to pass values up to its
        parent component. Example:

        ```python
        class AttributeBindingExample(rio.Component):
            toggle_is_on: bool = False

            def build(self) -> rio.Component:
                return rio.Column(
                    # Thanks to the attribute binding, toggling the Switch will
                    # also update this component's `toggle_is_on` attribute
                    rio.Switch(self.bind().toggle_is_on),
                    rio.Text("ON" if self.toggle_is_on else "OFF"),
                )
        ```

        For more details, see [Attribute Bindings](https://rio.dev/docs/howto/howto-get-value-from-child-component).
        """
        return AttributeBindingMaker(self)  # type: ignore

    def _custom_serialize_(self) -> JsonDoc:
        """
        Return any additional properties to be serialized, which cannot be
        deduced automatically from the type annotations.
        """
        return {}

    @abc.abstractmethod
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

    def _iter_referenced_components_(self) -> t.Iterable[Component]:
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
                for item in value:
                    if isinstance(item, Component):
                        yield item

    def _iter_direct_and_indirect_child_containing_attributes_(
        self,
        *,
        include_self: bool,
        recurse_into_high_level_components: bool,
    ) -> t.Iterable[Component]:
        from . import fundamental_component  # Avoid circular import problem

        # Special case the component itself to handle `include_self`
        if include_self:
            yield self

        if not recurse_into_high_level_components and not isinstance(
            self, fundamental_component.FundamentalComponent
        ):
            return

        # Iteratively yield all children
        to_do = list(self._iter_referenced_components_())
        while to_do:
            cur = to_do.pop()
            yield cur

            if recurse_into_high_level_components or isinstance(
                cur, fundamental_component.FundamentalComponent
            ):
                to_do.extend(cur._iter_referenced_components_())

    def _iter_component_tree_(
        self, *, include_root: bool = True
    ) -> t.Iterable[Component]:
        """
        Iterate over all components in the component tree, with this component as the root.
        """
        from . import fundamental_component  # Avoid circular import problem

        if include_root:
            yield self

        if isinstance(self, fundamental_component.FundamentalComponent):
            for child in self._iter_referenced_components_():
                yield from child._iter_component_tree_()
        else:
            build_result = self._build_data_.build_result  # type: ignore
            yield from build_result._iter_component_tree_()

    async def _on_message_(self, msg: Jsonable, /) -> None:
        raise RuntimeError(
            f"{type(self).__name__} received unexpected message `{msg}`"
        )

    def _is_in_component_tree_(
        self,
        cache: dict[rio.Component, bool],
    ) -> bool:
        """
        Returns whether this component is directly or indirectly connected to
        the component tree of a session. Components inside of a
        `DialogContainer` are also considered to be part of the component tree,
        even though they aren't technically child of any other in-tree
        component.

        This operation is fairly fast, but has to walk up the component tree to
        make sure the component's parent is also connected. Thus, when checking
        multiple components it can easily happen that the same components are
        checked over and over, resulting in `O(n log n)` runtime. To avoid this,
        pass a cache dictionary to this function, which will be used to memoize
        the result.

        Be careful not to reuse the cache if the component hierarchy might have
        changed (for example after an async yield).
        """

        # Already cached?
        try:
            return cache[self]
        except KeyError:
            pass

        # Root component?
        if self is self.session._high_level_root_component:
            result = True

        # If the builder has been garbage collected, the component must also be
        # dead.
        else:
            builder = self._weak_builder_()
            if builder is None:
                result = False

            # Even though the builder is alive, it may have since been rebuilt,
            # possibly orphaning this component.
            else:
                parent_data = builder._build_data_
                assert parent_data is not None
                result = (
                    self in parent_data.all_children_in_build_boundary
                    and builder._is_in_component_tree_(cache)
                )

        # Special case: `rio.DialogContainer`s are considered to be part of the
        # component tree as long as their owning component is.
        if not result and isinstance(
            self, rio.components.dialog_container.DialogContainer
        ):
            try:
                owning_component = self.session._weak_components_by_id[
                    self.owning_component_id
                ]
            except KeyError:
                result = False
            else:
                result = (
                    owning_component._is_in_component_tree_(cache)
                    and self._id_ in owning_component._owned_dialogs_
                )

        # Cache the result and return
        cache[self] = result
        return result

    @t.overload
    async def call_event_handler(
        self,
        handler: rio.EventHandler[[]],
    ) -> None: ...  # pragma: no cover

    @t.overload
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

        # TODO: This could really use an example

        await self.session._call_event_handler(
            handler, *event_data, refresh=False
        )

    def force_refresh(self) -> None:
        """
        Force a rebuild of this component.

        Most of the time components update automatically when their state
        changes. However, some state mutations are invisible to Rio: For
        example, appending items to a list modifies the list, but since no list
        instance was actually assigned to th component, Rio will be unaware of
        this change.

        In these cases, you can force a rebuild of the component by calling
        `force_refresh`. This will trigger a rebuild of the component and
        display the updated version on the screen.

        Another common use case is if you wish to update an component while an
        event handler is still running. Rio will automatically detect changes
        after event handlers return, but if you are performing a long-running
        operation, you may wish to update the component while the event handler
        is still running. This allows you to e.g. update a progress bar while
        the operation is still running.
        """
        self.session.create_task(self._force_refresh())

        # We need to return a custom Awaitable. We can't use a Task because that
        # would run regardless of whether the user awaits it or not, and we
        # can't use a Coroutine because python shows a warning if you don't
        # await a Coroutine
        class BackwardsCompat:
            async def complain_if_awaited(self):
                deprecations.warn(
                    since="0.10.9",
                    message="`force_refresh` is no longer async. Please call it without `await`.",
                )

            def __await__(self):
                return self.complain_if_awaited().__await__()

        return BackwardsCompat()  # type: ignore

    async def _force_refresh(self) -> None:
        """
        This function primarily exists for unit tests. Tests often need to wait
        until the GUI is refreshed, and the public `force_refresh()` doesn't
        allow that.
        """
        self.session._register_dirty_component(
            self,
            include_children_recursively=False,
        )

        await self.session._refresh()

    def _get_debug_details_(self) -> dict[str, t.Any]:
        """
        Used by Rio's dev tools to decide which properties to display to a user,
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
        result = f"<{type(self).__name__} id:{self._id_}"

        child_strings: list[str] = []
        for child in self._iter_referenced_components_():
            child_strings.append(f" {type(child).__name__}:{child._id_}")

        if child_strings:
            result += " -" + "".join(child_strings)

        return result + ">"

    def _repr_tree_worker_(self, file: t.IO[str], indent: str) -> None:
        file.write(indent)
        file.write(repr(self))

        for child in self._iter_referenced_components_():
            file.write("\n")
            child._repr_tree_worker_(file, indent + "    ")

    def _repr_tree(self) -> str:
        file = io.StringIO()
        self._repr_tree_worker_(file, "")
        return file.getvalue()

    @property
    def _effective_margin_left_(self) -> float:
        """
        Calculates the actual left margin of a component, taking into account
        the values of `margin`, `margin_x` and `margin_left`.
        """

        return utils.first_non_none(
            self.margin_left,
            self.margin_x,
            self.margin,
            0,
        )

    @property
    def _effective_margin_top_(self) -> float:
        """
        Calculates the actual top margin of a component, taking into account
        the values of `margin`, `margin_y` and `margin_top`.
        """

        return utils.first_non_none(
            self.margin_top,
            self.margin_y,
            self.margin,
            0,
        )

    @property
    def _effective_margin_right_(self) -> float:
        """
        Calculates the actual right margin of a component, taking into account
        the values of `margin`, `margin_right` and `margin_x`.
        """

        return utils.first_non_none(
            self.margin_right,
            self.margin_x,
            self.margin,
            0,
        )

    @property
    def _effective_margin_bottom_(self) -> float:
        """
        Calculates the actual bottom margin of a component, taking into account
        the values of `margin`, `margin_y` and `margin_bottom`.
        """

        return utils.first_non_none(
            self.margin_bottom,
            self.margin_y,
            self.margin,
            0,
        )
