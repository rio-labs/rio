# What's the difference between apps, sessions, and components?

## Apps

`rio.App` contains high level information about your website/app. Here you can
find the name, icon, pages and similar information. It also contains the build
function for creating your app's root component. You can access the app inside
of components via `self.session.app`.

There's only one instance of `rio.App` per app. Even if a hundred users are
connected, they all share the same `rio.App` instance.

## Sessions

Sessions contain information related to a single active user. When somebody
connects to your website via a browser, a new session is created for them. This
session contains information related to that user, such as their preferred
language, timezone, size of their window, etc.

If you're creating a local app, there will always be exactly one session.

Note that in practice a single person can have multiple sessions, if they e.g.
open your site on multiple devices, or multiple tabs.

Sessions are very frequently used throughout the app, e.g. for sharing values
between components, letting the user choose a file, and many other things.

## Components

Components are the building blocks of your app. They can be anything from a
simple button, a complex form, or even an entire page. Components can contain
state and expose events. They also have a `build` function, which constructs the
user interface for the component, by returning other, more fundamental
components.
