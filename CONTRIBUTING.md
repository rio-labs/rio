# Contribute to Rio

Rio is all about collaboration! It's an open-source project powered by the Rio team and awesome contributors like you. We appreciate your interest in making Rio even better.
Ready to jump in? We recommend checking out the [LICENSE](https://github.com/rio-labs/rio/blob/dev/LICENSE.txt) to understand how things work. All our code lives on GitHub, so you can easily see what's happening and get involved.

**Quick tip:** Chatting on discord with a maintainer before diving into a big pull request can save you time. That way, you can make sure your idea aligns with Rio's goals! Every contribution goes through the same fair review process, no matter who submits it.

## Feature Requests

Feature Requests by the community are highly encouraged. Feel free to submit a new one or upvote an existing feature request on [Github Discussions](https://github.com/rio-labs/rio/discussions/categories/feature-requests).

## Code of Conduct

This project, and everyone participating in it, are governed by Rio's Code of Conduct. By participating, you are expected to uphold it. Make sure to read the full text to understand which type of actions may or may not be tolerated.

## Bugs

Rio is using [GitHub issues](https://github.com/rio-labs/rio/issues) to manage bugs. We keep a close eye on them. Before filing a new issue, try to ensure your problem does not already exist.

<hr style="border:2px solid gray">

## Before Submitting a Pull Request

The Rio core team will review your pull request and either merge it, request changes, or close it.

### Prerequisites

-   You have [Python](https://www.python.org/) at `version 3.10 or higher` installed.
-   You have [Rye](https://rye.astral.sh/) at `version 0.33.0 or higher` installed.
-   You have [Node.js](https://nodejs.org/) at `version 20.0 or higher` installed.
-   You are familiar with [Git](https://git-scm.com/).

### Project structure

-   `frontend/` - TypeScript code for the Rio frontend
-   `raw-icons` - In addition to the official material icons, Rio ships with some
    of its own. This directory contains any and all custom icons.
-   `rio/` - Python code for the Rio backend
-   `scripts/` - Contains scripts which are tangentially related to Rio, but not
    used during runtime. For example, you can find benchmarking and publishing
    scripts here
-   `tests/` - Contains tests for Rio

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

## Miscellaneous

### Repository Organization

We chose to use a monorepo design. This allows us to maintain the whole ecosystem keep it up-to-date and consistent.

We do our best to keep the dev branch as clean as possible, with tests passing at all times. However, the dev branch can move faster than the release cycle. Therefore check the releases on [PyPI](https://pypi.org/project/rio-ui/) so that you are always up-to-date with the latest stable version.

### Reporting an issue

Before submitting an issue, please check the existing issues to see if your issue has already been reported. If it has, please add a comment to the existing issue instead of creating a new one.

-   You are experiencing a technical issue with Rio.
-   Your issue title is concise, on-topic, and polite.
-   You provide steps to reproduce the issue.
-   Make sure the issue template is respected.
-   Make sure your issue body is readable and [well formatted](https://docs.github.com/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).
