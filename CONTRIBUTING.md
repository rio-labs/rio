# Contribute to Rio

Rio is an open-source project administered by the Rio team. We appreciate your interest and efforts to contribute to Rio. See the [LICENSE](https://github.com/rio-labs/rio/blob/dev/LICENSE.txt) licensing information. All work done is available on GitHub.

We highly appreciate your effort to contribute, but we recommend you talking to a maintainer before spending a lot of time making a pull request that may not align with the project roadmap. Whether it is from the Rio team or contributors, every pull request goes through the same process.

## Feature Requests

Feature Requests by the community are highly encouraged. Feel free to submit a new one or upvote an existing feature request on [Github Discussions](https://github.com/rio-labs/rio/discussions/categories/feature-requests).

## Code of Conduct

This project, and everyone participating in it, are governed by Rio's Code of Conduct. By participating, you are expected to uphold it. Make sure to read the full text to understand which type of actions may or may not be tolerated.

## Bugs

Rio is using [GitHub issues](https://github.com/rio-labs/rio/issues) to manage bugs. We keep a close eye on them. Before filing a new issue, try to ensure your problem does not already exist.

<hr style="border:2px solid gray">

## Before Submitting a Pull Request

The Rio core team will review your pull request and either merge it, request changes, or close it.

### Contribution Prerequisites

-   You have [Python](https://www.python.org/) at `version 3.10 or higher` installed.
-   You have [Rye](https://rye-up.com/) at `version 0.33.0 or higher` installed.
-   You have [Node.js](https://nodejs.org/) at `version 20.0 or higher` installed.
-   You are familiar with [Git](https://git-scm.com/).

**Before submitting your pull request** make sure the following requirements are fulfilled:

-   Fork the repository and create your new branch from `dev`.
-   Run `rye sync` in the root of the repository.
-   Run `rye run dev-build` in the root of the repository. Or `npm run dev-build` if you are on Windows.
-   Make sure `pre-commit hooks` are installed by running `python -m pre_commit install`.
-   If your contribution fixes an existing issue, please make sure to link it in your pull request.

### Project structure

-   `frontend/` - TypeScript code for the Rio frontend
-   `raw-icons` - In addition to the official material icons, Rio ships with some
    of its own. This directory contains any and all custom icons.
-   `rio/` - Python code for the Rio backend
-   `scripts/` - Contains scripts which are tangentially related to Rio, but not
    used during runtime. For example, you can find benchmarking and publishing
    scripts here
-   `tests/` - Contains tests for Rio

## Development Workflow

While Rio allows users to write apps in 100% Python, Rio itself has both a
Python and a TypeScript component. In order to get started using Rio from the
repository, you'll have to build the typescript Component as well.

### 1. Fork the repository

[Go to the repository](https://github.com/rio-labs/rio) and fork it using your own GitHub account.

### 2. Clone the repository

```bash
git clone git@github.com:YOUR_USERNAME/rio.git
```

### 3. Install dependencies

Go to the root of the repository and run the setup:

```bash
cd rio
rye sync
rye run dev-build
python -m pre_commit install
```

Rye and npm don't get along well on windows. If the build command above fails,
try to build directly using `npm`:

```bash
npm run dev-build
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
-   Make sure your issue body is readable and [well formatted](https://docs.github.com/de/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).
