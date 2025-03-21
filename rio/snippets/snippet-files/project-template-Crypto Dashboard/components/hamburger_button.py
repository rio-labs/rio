import rio


# <component>
class HamburgerButton(rio.Component):
    """
    A toggleable hamburger button component.

    This component displays a hamburger menu icon when the menu is closed and a
    close icon when the menu is open. It allows toggling the `is_open` state
    through a pointer (click/touch) event.


    ## Attributes:

    `is_open`: Indicates whether the menu is currently open or closed.
    """

    is_open: bool = False

    def _on_toggle_open(self, _: rio.PointerEvent) -> None:
        """
        Handles the toggle action when the button is pressed.

        This method toggles the `is_open` state between `True` and `False`.
        """
        self.is_open = not self.is_open

    def build(self) -> rio.Component:
        """
        Builds the hamburger button component.

        The button dynamically changes its icon and appearance based on the
        `is_open` state.
        """
        # Determine the icon and fill color based on the open state
        if self.is_open:
            # Display a close icon when the menu is open
            icon = "material/close"
            fill = self.session.theme.text_style.fill
        else:
            # Display a hamburger menu icon when closed
            icon = "material/menu"
            fill = self.session.theme.text_style.fill

        # Ensure the fill is a valid rio.Color instance
        assert isinstance(fill, rio.Color)

        return rio.PointerEventListener(
            rio.Rectangle(
                content=rio.Icon(
                    icon=icon,
                    fill=fill,
                    min_width=2.2,
                    min_height=2.2,
                ),
                fill=rio.Color.TRANSPARENT,
                # Show pointer cursor on hover
                cursor="pointer",
            ),
            on_press=self._on_toggle_open,
        )


# </component>
