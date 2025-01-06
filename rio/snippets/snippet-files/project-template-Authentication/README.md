This template demonstrates how to implement user authentication in your app. It
uses SQLite to store user data, but you are of course free to replace it with
whichever persistence mechanism you prefer.

## Outline 📝

All database access is done using a `Persistence` class. This abstracts away the
database operations and makes it easy to switch to a different database if
needed. This class is attached to the session to make it easily retrievable
throughout the app.

When a user logs in, two things happen:

- A session token is stored on the user's device so the user can be recognized
  on subsequent visits.
- Information about the user, such as their ID and username are attached to the
  session. This indicates to the app that somebody is logged in, and who that
  person is.

Any pages that shouldn't be accessible without logging in are protected using
Rio's guard mechanism.
