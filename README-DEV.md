# Getting started

While Rio allows users to write apps in 100% Python, Rio itself has both a
Python and a TypeScript component. In order to get started using Rio from the
repository, you'll have to build the typescript Component as well. Here's the
commands:

```bash
git clone git@github.com:rio-labs/rio.git
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

## Project structure

- `frontend/` - TypeScript code for the Rio frontend
- `prototyping` - Contains a bunch of random files used during development. To
  be honest, we probably shouldn't be committing this folder :/
- `raw-icons` - In addition to the official material icons, Rio ships with some
  of its own. This directory contains any and all custom icons.
- `rio/` - Python code for the Rio backend
- `scripts/` - Contains scripts which are tangentially related to Rio, but not
  used during runtime. For example, you can find benchmarking and publishing
  scripts here
- `tests/` - Duh.
