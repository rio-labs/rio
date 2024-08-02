# Contribute to Rio

Rio is all about collaboration! It's an open-source project powered by the Rio
team and awesome contributors like you. We appreciate your interest in making
Rio even better. Ready to jump in? We recommend checking out the
[LICENSE](https://github.com/rio-labs/rio/blob/dev/LICENSE.txt) to understand
how things work. All our code lives on GitHub, so you can easily see what's
happening and get involved.

**Quick tip:** Chatting on discord with a maintainer before diving into a big
pull request can save you time. That way, you can make sure your idea aligns
with Rio's goals! Every contribution goes through the same fair review process,
no matter who submits it.

## Feature Requests

Feature Requests by the community are highly encouraged. Feel free to submit a
new one or upvote an existing feature request on [Github
Discussions](https://github.com/rio-labs/rio/discussions/categories/feature-requests).

## Code of Conduct

This project, and everyone participating in it, are governed by Rio's Code of
Conduct. By participating, you are expected to uphold it. Make sure to read the
full text to understand which type of actions may or may not be tolerated.

## Bugs

Rio is using [GitHub issues](https://github.com/rio-labs/rio/issues) to manage
bugs. We keep a close eye on them. Before filing a new issue, try to ensure your
problem does not already exist.

<hr style="border:2px solid gray">

## Before Submitting a Pull Request

The Rio core team will review your pull request and either merge it, request
changes, or close it.

### Prerequisites

- You have [Python](https://www.python.org/) at `version 3.10 or higher`
  installed.
- You have [Rye](https://rye.astral.sh/) at `version 0.33.0 or higher`
  installed.
- You have [Node.js](https://nodejs.org/) at `version 20.0 or higher` installed.
- You are familiar with [Git](https://git-scm.com/).

### Project structure

- `frontend/` - TypeScript code for the Rio frontend
- `raw-icons` - In addition to the official material icons, Rio ships with some
    of its own. This directory contains any and all custom icons.
- `rio/` - Python code for the Rio backend
- `scripts/` - Contains scripts which are tangentially related to Rio, but not
    used during runtime. For example, you can find benchmarking and publishing
    scripts here
- `tests/` - Contains tests for Rio

### Development Setup

While Rio allows users to write apps in 100% Python, Rio itself has both a
Python and a TypeScript component. In order to get started using Rio from the
repository, you'll have to build the typescript Component as well.

### 1. Fork the repository

[Go to the repository](https://github.com/rio-labs/rio) and fork it using your
own GitHub account.

### 2. Clone the repository

```bash
git clone git@github.com:YOUR_USERNAME/rio.git
```

### 3. Set up the environment

Use rye to install all Python dependencies:

```bash
rye sync
```

Make sure the pre-commit hooks are installed. These will run some basic checks
before creating commits:

```bash
python -m pre_commit install
```

Install dev dependencies using `npm`:

```bash
npm install
```

Some developers have reported that they must explicitly import `sass`. If you
run into issues, try running:

```bash
npm install sass
```

Build the frontend:

```bash
rye run dev-build
```

## Conventions & Consistency

As projects grow, it's easy for inconsistencies to creep in. Similar functions
use different names. The same concept is implemented in multiple ways, that sort
of things. The only thing worse than a bad solution is two good ones.

To avoid this, we've decided on a few conventions used throughout Rio:

- Event handlers are always written in present tense: `on_change`, `on_move`,
  etc., NOT past tense (`on_changed`, `on_moved`).

- Whenever a value has physical units attached, prefer to use SI base units. For
  example, measure time in seconds, not milliseconds.

  Occasionally it can make sense to break this rule. For example, when
  configuring how long a cache lasts, users will have a hard time understanding
  a duration of days, when expressed in seconds. If you do decide to use a
  different unit, always make that clear, by including the unit in the name
  (e.g. `cache_duration_days`).

  Sometimes the library/language you're in already has a well established class
  for this. For example, in Python the built-in `timedelta` class would be
  preferable to all of the above. This way times can be expressed in any unit
  the user prefers.

- Avoid negatives. For example, use `is_visible` instead of `is_hidden`. Nobody
  likes to think around corners. Here's some more examples

  - `is_visible` instead of `is_hidden`
  - `is_sensitive` instead of `is_insensitive`
  - `is_active` instead of `is_disabled`

  Along the same lines, **absolutely avoid double negatives**. Never, ever, ever
  use names like `is_not_hidden` or `dont_hide_something`.

- Python code follows Python naming conventions, such as all_lower_case for
  variables and functions, and CamelCase for classes.

  JavaScript, TypeScript & JSON follow JavaScript naming conventions, such as
  camelCase for variables and functions, and UpperCamelCase for classes.

  Files use all_lower_case.

- When naming a dictionary after its contents, name it `keys_to_values`, rather
  than e.g. `values_by_key`. For example, `ids_to_instances` or `names_to_id`.
  It is of course also perfectly fine to use a different name if it makes more
  sense in your particular context.

  As this is a fairly new addition, there is still dictionaries in the codebase
  that don't stick to this convention. Feel free to report and/or change them if
  you spot any.

## Reporting Issues

Before submitting an issue, please check the existing issues to see if your
issue has already been reported. If it has, please add a comment to the existing
issue instead of creating a new one.

- You are experiencing a technical issue with Rio.
- Your issue title is concise, on-topic, and polite.
- You provide steps to reproduce the issue.
- Make sure the issue template is respected.
- Make sure your issue body is readable and [well formatted](https://docs.github.com/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).
