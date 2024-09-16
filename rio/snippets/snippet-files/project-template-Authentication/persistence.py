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

    User data is stored in the 'users' table, and session data is stored in the 'user_sessions' table.

    You can easyly adapt this class to your needs by adding more methods to interact with the database
    or support different databases like MongoDB.

    Attributes:
        `db_path`: Path to the SQLite database file
    """

    def __init__(self, db_path: Path = Path("user.db")) -> None:
        """
        Initialize the Persistence instance and ensure necessary tables exist.
        """
        self.conn = sqlite3.connect(db_path)
        self._create_user_table()  # Ensure the users table exists
        self._create_session_table()  # Ensure the sessions table exists

    # Private method to create the users table if it doesn't exist
    def _create_user_table(self) -> None:
        """
        Create the 'users' table in the database if it does not exist.
        The table stores user information including id, username, timestamps, and password data.
        """
        cursor = (
            self.conn.cursor()
        )  # Create a cursor object to execute SQL commands
        # Store dates as floats (UNIX timestamps)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                last_login REAL NOT NULL, 
                created_at REAL NOT NULL,
                password_hash BLOB NOT NULL,
                password_salt BLOB NOT NULL
            )
        """
        )  # SQL command to create the table
        self.conn.commit()  # Save the changes

    # Private method to create the session table if it doesn't exist
    def _create_session_table(self) -> None:
        """
        Create the 'user_sessions' table in the database if it does not exist.
        The table stores session information including session id, user id, and timestamps.
        """
        # conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        # Store dates as floats (UNIX timestamps)
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
        self.conn.commit()

    # Method to add a new user to the database
    async def add_user(self, user: data_models.LoggedInUser) -> None:
        """
        Add a new user to the database.

        Args:
            `user`: The user object containing user details.
        """
        # Create a cursor object to execute SQL commands
        cursor = self.conn.cursor()
        # SQL command to insert a new user into the table
        cursor.execute(
            """
            INSERT INTO users (id, username, last_login, created_at, password_hash, password_salt)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                str(user.id),  # TODO: int
                user.username,
                user.last_login.timestamp(),
                user.created_at.timestamp(),
                user.password_hash,
                user.password_salt,
            ),
        )
        self.conn.commit()

    # Method to retrieve a user by username
    async def get_user_by_username(
        self, username: str
    ) -> data_models.LoggedInUser | None:
        """
        Retrieve a user from the database by username.

        Args:
            `username`: The username of the user to retrieve.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()

        if row:
            return data_models.LoggedInUser(
                id=uuid.UUID(row[0]),
                username=row[1],
                last_login=datetime.fromtimestamp(row[2], tz=timezone.utc),
                created_at=datetime.fromtimestamp(row[3], tz=timezone.utc),
                password_hash=row[4],
                password_salt=row[5],
            )
        else:
            return None  # Return None if user not found

    async def get_user_by_id(
        self, id: uuid.UUID
    ) -> data_models.LoggedInUser | None:
        """
        Retrieve a user from the database by user ID.

        Args:
            `id`: The UUID of the user to retrieve.
        """
        cursor = self.conn.cursor()
        # SQL command to get user by ID
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(id),))
        row = cursor.fetchone()
        if row:
            return data_models.LoggedInUser(
                id=uuid.UUID(row[0]),
                username=row[1],
                last_login=datetime.fromtimestamp(row[2], tz=timezone.utc),
                created_at=datetime.fromtimestamp(row[3], tz=timezone.utc),
                password_hash=row[4],
                password_salt=row[5],
            )
        else:
            return None  # Return None if user not found

    # Method to add a new session
    async def create_session(
        self, user_id: uuid.UUID
    ) -> data_models.UserSession:
        """
        Create a new user session and store it in the database.

        Args:
            `user_id`: The UUID of the user for whom to create the session.
        """
        now = datetime.now(tz=timezone.utc)

        session = data_models.UserSession(
            id=secrets.token_urlsafe(),
            user_id=user_id,
            created_at=now,
            valid_until=now + timedelta(days=1),
        )

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

        return session

    async def extend_session_duration(
        self, auth_token: str, new_valid_until: timedelta = timedelta(days=1)
    ) -> None:
        """
        Extend the duration of an existing session.

        Args:
            `auth_token`: The authentication token (session ID) of the session to extend.
            `new_valid_until`: The new duration to extend the session by. Defaults to 1 day.
        """
        now = datetime.now(tz=timezone.utc)
        cursor = self.conn.cursor()

        # Update the session's valid_until field with new timestamp
        cursor.execute(
            """
            UPDATE user_sessions
            SET valid_until = ?
            WHERE id = ?
            """,
            (
                (now + new_valid_until).timestamp(),
                auth_token,
            ),
        )
        self.conn.commit()

    # Method to retrieve sessions by user ID
    async def get_sessions_by_auth_token(
        self, auth_token: str
    ) -> data_models.UserSession:
        """
        Retrieve a user session from the database by authentication token.

        Args:
            `auth_token`: The authentication token (session ID) of the session to retrieve.
        """
        # Connect to the database
        cursor = self.conn.cursor()

        # Construct the SQL query

        cursor.execute(
            "SELECT * FROM user_sessions WHERE id = ? ORDER BY created_at LIMIT 1",
            (auth_token,),
        )

        row = cursor.fetchone()

        if not row:
            raise KeyError(auth_token)

        return data_models.UserSession(
            id=row[0],
            user_id=uuid.UUID(row[1]),
            created_at=datetime.fromtimestamp(row[2], tz=timezone.utc),
            valid_until=datetime.fromtimestamp(row[3], tz=timezone.utc),
        )
