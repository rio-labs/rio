# <additional-imports>
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import *  # type: ignore

import rio

from . import data_models, persistence

# </additional-imports>


# <additional-code>
async def on_app_start(app: rio.App) -> None:
    print("LogLog: App started")
    pers = persistence.Persistence()
    # attach the persistence to the app
    # This way, the persistence instance is available to all components
    # using `session[persistence.Persistence]`
    app.default_attachments.append(pers)


async def on_session_start(session: rio.Session) -> None:
    print("LogLog: Session started")
    # Check if this user has a valid auth token
    user_settings = session[data_models.UserSettings]

    if user_settings.auth_token:
        pers = session[persistence.Persistence]

        try:
            user_session = await pers.get_sessions_by_auth_token(
                user_settings.auth_token,
            )

        # Nope, invalid session
        except KeyError:
            print(
                f"LogLog: No session found for token `{user_settings.auth_token}`"
            )

        # Yes!
        else:
            print(
                f"LogLog: Found session for token `{user_settings.auth_token}`"
            )
            # Check if the session is still valid
            if user_session.valid_until < datetime.now(tz=timezone.utc):
                print(
                    f"LogLog: Session `{user_settings.auth_token}` has expired"
                )
                # Expire the session

            else:
                print(
                    f"LogLog: Session `{user_settings.auth_token}` is still valid"
                )
                # Attach the session
                session.attach(user_session)

                # For a user to be considered logged in, a `UserInfo` also needs to
                # be attached.
                userinfo = await pers.get_user_by_id(user_session.user_id)
                session.attach(userinfo)

                # This session has only just been used. Extend its duration
                await pers.extend_session_duration(
                    user_session.id,
                    new_valid_until=timedelta(days=1),
                )


# </additional-code>
