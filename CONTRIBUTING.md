# Contribute to Rio

Rio is all about collaboration! It's an open-source project powered by the Rio
team and awesome contributors like you. We appreciate your interest in making
Rio even better. Ready to jump in? We recommend checking out the
[LICENSE](https://github.com/rio-labs/rio/blob/main/LICENSE.txt) to understand
how things work. All our code lives on GitHub, so you can easily see what's
happening and get involved.

**Quick tip:** [A quick chat on discord](https://discord.gg/7ejXaPwhyH) with a
maintainer before diving into a big pull request can save you time. That way,
you can make sure your idea aligns with Rio's goals! We're very active on
discord - you can expect to get an answer in minutes when we aren't asleep.

## Feature Requests

Feature Requests by the community are highly encouraged. Feel free to submit a
new one or upvote an existing feature request on [Github
Discussions](https://github.com/rio-labs/rio/discussions/categories/feature-requests).

## Bugs

Rio is using [GitHub issues](https://github.com/rio-labs/rio/issues) to manage
bugs. We keep a close eye on them. Before filing a new issue, try to ensure your
problem does not already exist.

## Before Submitting a Pull Request

The Rio core team will review your pull request and either merge it, request
changes, or close it.

### Prerequisites

-   You have [Python](https://www.python.org/) version 3.10 or higher
    installed
-   You have [Uv](https://docs.astral.sh/uv/getting-started/installation/)
    version 0.6.5 or higher installed
-   You have [Node.js](https://nodejs.org/) version 20.0 or higher installed
-   You are familiar with [Git](https://git-scm.com/)

### Project structure

-   `frontend/` - TypeScript code for the Rio frontend
-   `raw-icons/` - In addition to the official material icons, Rio ships with some
    of its own. This directory contains any and all custom icons.
-   `rio/` - Python code for the Rio backend
-   `scripts/` - Contains scripts which are tangentially related to Rio, but not
    used during runtime. For example, you can find benchmarking and publishing
    scripts here
-   `tests/` - Contains tests for Rio

### Development Setup

### 1. Fork the repository

[Go to the repository](https://github.com/rio-labs/rio) and fork it using your
own GitHub account.

### 2. Clone the repository

```bash
git clone git@github.com:YOUR_USERNAME/rio.git
```

### 3. Set up the environment

`cd` into your freshly cloned rio folder:

```bash
cd rio
```

Use uv to install all Python dependencies:

```bash
uv sync --all-extras
```

(`--all-extras` will install everything necessary for local apps to work in
addition to websites. Since some of this functionality is tested in the test
suite, tests would fail without installing these dependencies.)

Make sure the pre-commit hooks are installed. These will run some basic checks
before creating commits:

```bash
python -m pre_commit install
```

While Rio allows users to write apps in 100% Python, Rio itself has both a
Python and a TypeScript component. In order to get started using Rio from the
repository, you'll have to build the typescript Component first

Install dev dependencies using `npm`:

```bash
npm install
```

Now build the frontend:

```bash
uv run scripts/build.py
```

## Conventions & Consistency

As projects grow, it's easy for inconsistencies to creep in. Similar functions
use different names. The same concept is implemented in multiple ways, that sort
of things. The only thing worse than a bad solution is two good ones.

To avoid this, we've decided on a few conventions used throughout Rio:

-   Event handlers are always written in present tense: `on_change`, `on_move`,
    etc., NOT past tense (`on_changed`, `on_moved`).

-   Whenever a value has physical units attached, prefer to use SI base units. For
    example, durations are measured in seconds, not milliseconds.

    Occasionally it can make sense to break this rule. For example, when
    configuring how long a cache lasts, users will have a hard time
    understanding a duration on the order of days expressed in seconds. If you
    do decide to use a different unit, always make that clear, by including the
    unit in the name (e.g. `cache_duration_in_days`).

    Sometimes the library/language you're in already has a well established
    class for this. For example, in Python the built-in `timedelta` class would
    be preferable to all of the above. This way times can be expressed in any
    unit the user prefers.

-   Avoid negatives. For example, use `is_visible` instead of `is_hidden`. Nobody
    likes to think around corners. Here's some more examples

    -   `is_visible` instead of `is_hidden`
    -   `is_sensitive` instead of `is_insensitive`
    -   `is_active` instead of `is_disabled`

        Along the same lines, **absolutely avoid double negatives**. Never, ever,
        ever use names like `is_not_hidden` or `dont_hide_something`.

-   Python code follows Python naming conventions, such as all_lower_case for
    variables and functions, and CamelCase for classes.

    JavaScript, TypeScript & JSON follow JavaScript naming conventions, such as
    camelCase for variables and functions, and UpperCamelCase for classes.

    Files use all_lower_case.

-   When naming a dictionary after its contents, name it `keys_to_values`, rather
    than e.g. `values_by_key`. For example, `ids_to_instances` or `names_to_id`.
    It is of course also perfectly fine to use a different name if it makes more
    sense in your particular context.

    As this is a fairly new addition, there is still dictionaries in the codebase
    that don't stick to this convention. Feel free to report and/or change them if
    you spot any.

-   _In general,_ avoid importing values from modules. Import the modules
    themselves, then include the module name when accessing values. Also avoid
    renaming modules when imported.

    ```python
    # Do this
    import traceback
    traceback.print_exc()

    # Not this
    from traceback import print_exc
    print_exc()

    # Or this
    import traceback as tb
    tb.print_exc()
    ```

    A little bit of verbosity beats having to constantly think about whether a
    value is available as `foo` or `foo.bar` in each file.

    This has limits however. Some modules, types & functions are so common that
    the rules above can lead to unreadable code. Here are some conventions that
    have been established over time:

    ```python
    # These are fine, and encouraged
    from __future__ import annotations

    from datetime import datetime, timezone, timedelta
    from pathlib import Path

    import typing as t
    import typing_extensions as te

    import numpy as np
    import pandas as pd
    import polars as pl

    # In Rio projects specifically
    import components as comps
    ```

-   **Use type hints!** They don't take long to type, but help out **you**, anyone
    else reading your code, and most importantly, your type checker. They really
    pay off in the long run. Not to mention that they force you to think about
    your data models a bit more critically, leading to better code.
