import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import data_models as data_models


# Define the UserPersistence dataclass to handle database operations
class Persistence:
    """
    A class to handle database operations for users and sessions.

    User data is stored in the 'users' table, and session data is stored in the
    'user_sessions' table.

    You can adapt this class to your needs by adding more methods to interact
    with the database or support different databases like MongoDB.

    ## Attributes

    `db_path`: Path to the SQLite database file
    """

    def __init__(self, db_path: Path) -> None:
        """
        Initialize the Persistence instance and ensure necessary tables exist.
        """
        self.conn = sqlite3.connect(db_path)
        self._create_user_table()  # Ensure the users table exists
        self._create_session_table()  # Ensure the sessions table exists

    def _create_user_table(self) -> None:
        """
        Create the 'users' table in the database if it does not exist. The table
        stores user information including id, username, timestamps, and password
        data.
        """
        # Create a cursor object to execute SQL commands
        cursor = self.conn.cursor()

        # We'll store dates as floats (UNIX timestamps), since SQLite doesn't
        # have a native datetime type. Floats are easy to compare and convert,
        # so they work well for this purpose.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at REAL NOT NULL,
                password_hash BLOB NOT NULL,
                password_salt BLOB NOT NULL
            )
        """
        )

        # Commit the changes
        self.conn.commit()

    def _create_session_table(self) -> None:
        """
        Create the 'user_sessions' table in the database if it does not exist.
        The table stores session information including session id, user id, and
        timestamps.
        """
        # Create a cursor object to execute SQL commands
        cursor = self.conn.cursor()

        # Create the user_sessions table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                valid_until REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """
        )

        # Commit the changes
        self.conn.commit()

    async def create_user(self, user: data_models.AppUser) -> None:
        """
        Add a new user to the database.

        ## Parameters

        `user`: The user object containing user details.
        """
        # Create a cursor object to execute SQL commands
        cursor = self.conn.cursor()

        # SQL command to insert a new user into the table
        cursor.execute(
            """
            INSERT INTO users (id, username, created_at, password_hash, password_salt)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(user.id),
                user.username,
                user.created_at.timestamp(),
                user.password_hash,
                user.password_salt,
            ),
        )

        # Commit the changes
        self.conn.commit()

    async def get_user_by_username(
        self,
        username: str,
    ) -> data_models.AppUser:
        """
        Retrieve a user from the database by username.


        ## Parameters

        `username`: The username of the user to retrieve.


        ## Raises

        `KeyError`: If there is no user with the specified username.
        """
        # Look up the user in the database
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ? LIMIT 1",
            (username,),
        )

        # Get the first row from the result
        row = cursor.fetchone()

        # If a user was found, wrap it up in a neat Python class
        if row:
            return data_models.AppUser(
                id=uuid.UUID(row[0]),
                username=row[1],
                created_at=datetime.fromtimestamp(row[2], tz=timezone.utc),
                password_hash=row[3],
                password_salt=row[4],
            )

        # If no user was found, signal that with a KeyError
        raise KeyError(username)

    async def get_user_by_id(
        self,
        id: uuid.UUID,
    ) -> data_models.AppUser:
        """
        Retrieve a user from the database by user ID.


        ## Parameters

        `id`: The UUID of the user to retrieve.


        ## Raises

        `KeyError`: If there is no user with the specified ID.
        """
        # Create a cursor object to execute SQL commands
        cursor = self.conn.cursor()

        # SQL command to get user by ID
        cursor.execute(
            "SELECT * FROM users WHERE id = ? LIMIT 1",
            (str(id),),
        )

        # Get the first row from the result
        row = cursor.fetchone()

        # If a user was found, wrap it up in a neat Python class
        if row:
            return data_models.AppUser(
                id=uuid.UUID(row[0]),
                username=row[1],
                created_at=datetime.fromtimestamp(row[2], tz=timezone.utc),
                password_hash=row[3],
                password_salt=row[4],
            )

        # If no user was found, signal that with a KeyError
        raise KeyError(id)

    async def create_session(
        self,
        user_id: uuid.UUID,
    ) -> data_models.UserSession:
        """
        Create a new user session and store it in the database.

        ## Parameters

        `user_id`: The UUID of the user for whom to create the session.
        """
        # Store the time in a variable. It will be used multiple times, and this
        # ensures that all timestamps are consistent.
        now = datetime.now(tz=timezone.utc)

        # Create the new session object
        session = data_models.UserSession(
            id=secrets.token_urlsafe(),
            user_id=user_id,
            created_at=now,
            valid_until=now + timedelta(days=1),
        )

        # Store the session in the database
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_sessions (id, user_id, created_at, valid_until)
            VALUES (?, ?, ?, ?)
            """,
            (
                session.id,
                str(session.user_id),
                session.created_at.timestamp(),
                session.valid_until.timestamp(),
            ),
        )
        self.conn.commit()

        # Return the freshly created session
        return session

    async def update_session_duration(
        self,
        session: data_models.UserSession,
        new_valid_until: datetime,
    ) -> None:
        """
        Extend the duration of an existing session. This will update the
        session's validity timestamp both in the given object and the database.

        ## Parameters

        `session`: The session whose duration to extend.

        `new_valid_until`: The new timestamp until which the session should be
            considered valid.
        """
        # Update the session object
        session.valid_until = new_valid_until

        # Commit the changes to persistence
        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE user_sessions
            SET valid_until = ?
            WHERE id = ?
            """,
            (
                session.valid_until.timestamp(),
                session.id,
            ),
        )
        self.conn.commit()

    async def get_session_by_auth_token(
        self,
        auth_token: str,
    ) -> data_models.UserSession:
        """
        Retrieve a user session from the database by authentication token.

        ## Parameters

        `auth_token`: The authentication token (session ID) of the session to
            retrieve.

        ## Raises

        `KeyError`: If there is no session with the specified authentication
        token.
        """
        # Create a cursor object to execute SQL commands
        cursor = self.conn.cursor()

        # Query the database for the session
        cursor.execute(
            "SELECT * FROM user_sessions WHERE id = ? ORDER BY created_at LIMIT 1",
            (auth_token,),
        )

        # Get the first row from the result
        row = cursor.fetchone()

        # If a session was found, wrap it up in a neat Python class
        if row:
            return data_models.UserSession(
                id=row[0],
                user_id=uuid.UUID(row[1]),
                created_at=datetime.fromtimestamp(row[2], tz=timezone.utc),
                valid_until=datetime.fromtimestamp(row[3], tz=timezone.utc),
            )

        # If no session was found, signal that with a KeyError
        raise KeyError(auth_token)

    async def delete_session(
        self,
        session_id: str,
    ) -> None:
        """
        Delete a user session from the database by its ID.

        ## Parameters

        `session_id`: The ID of the session to delete.
        """
        # Create a cursor object to execute SQL commands
        cursor = self.conn.cursor()

        # SQL command to delete the session
        cursor.execute(
            "DELETE FROM user_sessions WHERE id = ?",
            (session_id,),
        )

        # Commit the changes
        self.conn.commit()
