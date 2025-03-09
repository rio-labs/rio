import abc
import dataclasses

from .component import Component
from .fundamental_component import FundamentalComponent

__all__ = [
    "KeyboardFocusableComponent",
    "KeyboardFocusableFundamentalComponent",
]


class KeyboardFocusableComponent(Component, abc.ABC):
    """
    ## Attributes

    `auto_focus`: Whether this component should receive the keyboard focus when
        it is created.

    ## Metadata

    `public`: False
    """

    _: dataclasses.KW_ONLY
    auto_focus: bool = False

    @abc.abstractmethod
    async def grab_keyboard_focus(self) -> None:
        """
        ## Metadata

        `public`: False
        """
        raise NotImplementedError


class KeyboardFocusableFundamentalComponent(
    KeyboardFocusableComponent, FundamentalComponent
):
    async def grab_keyboard_focus(self) -> None:
        """
        ## Metadata

        `public`: False
        """
        await self.session._remote_set_keyboard_focus(self._id_)
