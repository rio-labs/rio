import hashlib
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import rio


@dataclass
class UserSettings(rio.UserSettings):
    """
    Model for data stored client-side for each user.
    """

    # The (possibly expired) authentication token for this user. If this matches
    # the id of any valid `UserSession`, it is safe to consider the user as
    # authenticated being in that session.
    #
    # (Prevents users from having to log-in again each time the page is
    # accessed.)

    auth_token: str


@dataclass
class UserSession:
    # Unique ID, as well as the session's token; url safe
    id: str

    # The user this session belongs to
    user_id: uuid.UUID

    # When this session was created
    created_at: datetime

    # Until when this session is valid
    valid_until: datetime


@dataclass
class LoggedInUser:
    id: uuid.UUID
    username: str
    last_login: datetime
    created_at: datetime
    password_hash: bytes
    password_salt: bytes

    @classmethod
    def new_with_defaults(cls, username, password) -> "LoggedInUser":
        password_salt = os.urandom(64)
        return LoggedInUser(
            id=uuid.uuid4(),
            username=username,
            last_login=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            password_hash=cls.get_password_hash(password, password_salt),
            password_salt=password_salt,
        )

    @classmethod
    def get_password_hash(cls, password, password_salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            password_salt,
            100000,
        )

    def password_equals(self, password: str) -> bool:
        return secrets.compare_digest(
            self.password_hash,
            self.get_password_hash(password, self.password_salt),
        )
