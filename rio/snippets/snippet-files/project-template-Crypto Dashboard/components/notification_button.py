import rio


# <component>
class NotificationButton(rio.Component):
    """
    A component representing a notification button with an icon and a red badge.

    The NotificationButton features a bell icon, a red circular badge to
    indicate new notifications, and hover effects to enhance interactivity.
    """

    def build(self) -> rio.Component:
        # Create a stack with the notification icon and badge
        content = rio.Stack(
            # Notification icon (bell symbol)
            rio.Icon(
                "material/notifications",
                min_height=1.6,
                min_width=1.6,
                margin=0.5,
            ),
            # Notification badge (red circular indicator)
            rio.Rectangle(
                fill=rio.Color.RED,
                corner_radius=9999,
                align_x=0.7,
                align_y=0.25,
                min_width=0.7,
                min_height=0.7,
                stroke_width=0.15,
                stroke_color=self.session.theme.background_color,
            ),
        )

        # Wrap the stack in a rectangle for hover and click effects
        return rio.Rectangle(
            content=content,
            fill=rio.Color.TRANSPARENT,
            hover_fill=self.session.theme.neutral_color,
            corner_radius=self.session.theme.corner_radius_small,
            transition_time=0.1,
            cursor="pointer",
            align_y=0.5,
        )


# </component>
