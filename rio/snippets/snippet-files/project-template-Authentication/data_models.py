from __future__ import annotations

import dataclasses
import hashlib
import os
import secrets
import uuid
from datetime import datetime, timezone

import rio


@dataclasses.dataclass
class UserSettings(rio.UserSettings):
    """
    Model for data stored client-side for each user.
    """

    # The (possibly expired) authentication token for this user. If this matches
    # the id of any valid `UserSession`, it is safe to consider the user as
    # authenticated being in that session.
    #
    # This prevents users from having to log-in again each time the page is
    # accessed.
    auth_token: str


@dataclasses.dataclass
class UserSession:
    # This ID uniquely identifies the session. It also serves as the
    # authentication token for the user.
    id: str

    # The user this session belongs to
    user_id: uuid.UUID

    # When this session was initially created
    created_at: datetime

    # Until when this session is valid
    valid_until: datetime


@dataclasses.dataclass
class AppUser:
    """
    Model for a user of the application.
    """

    # A unique identifier for this user
    id: uuid.UUID

    # The user's chosen username
    username: str

    # When the user account was created
    created_at: datetime

    # The hash and salt of the user's password. By storing these values we can
    # verify that a user entered the correct password without storing the actual
    # password in the database. Google "hashing & salting" for details if you're
    # curious.
    password_hash: bytes
    password_salt: bytes

    @classmethod
    def new_with_defaults(cls, username, password) -> AppUser:
        """
        Create a new user with the given username and password, filling in
        reasonable defaults for the other fields.
        """

        password_salt = os.urandom(64)

        return AppUser(
            id=uuid.uuid4(),
            username=username,
            created_at=datetime.now(timezone.utc),
            password_hash=cls.get_password_hash(password, password_salt),
            password_salt=password_salt,
        )

    @classmethod
    def get_password_hash(cls, password, password_salt: bytes) -> bytes:
        """
        Compute the hash of a password using a given salt.
        """
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            password_salt,
            100000,
        )

    def password_equals(self, password: str) -> bool:
        """
        Safely compare a password to the stored hash. This differs slightly from
        the `==` operator in that it is resistant to timing attacks.
        """
        return secrets.compare_digest(
            self.password_hash,
            self.get_password_hash(password, self.password_salt),
        )
