# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Rio is a Python-first web framework for building websites and apps entirely in Python (no HTML/CSS/JavaScript required). It uses a React-like component model with a hybrid architecture:
- **Python backend**: Component definitions, logic, state management, server communication
- **TypeScript frontend**: DOM rendering, event handling, client interactions
- **Communication**: WebSocket/HTTP RPC between Python and TypeScript

## Development Commands

### Initial Setup
```bash
# Install Python dependencies (required first)
uv sync --all-extras

# Install frontend dependencies
npm install

# Build frontend (REQUIRED before first use and after TypeScript changes)
npm run build

# Install pre-commit hooks
python -m pre_commit install
```

### Building
```bash
# Development build (default)
npm run dev-build

# Production build (for releases)
npm run build
```

**When to rebuild frontend**: After any changes to TypeScript/SCSS files in `/frontend/`, before testing, and before releases.

### Testing
```bash
# Run all Python tests
uv run pytest

# Run specific test file
uv run pytest tests/test_components.py

# Run with coverage
uv run scripts/code_coverage.py

# Frontend integration tests (requires browser setup)
uv run pytest tests/test_frontend/
```

### Code Quality
```bash
# Lint Python code
python -m ruff check .

# Format Python code
python -m ruff format .

# Format TypeScript code
npx prettier --write frontend/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Running Rio Apps
```bash
# Create new project from template
rio new

# Run project in development mode
rio run

# Run in browser vs window
app.run_in_browser()  # Web app
app.run_in_window()   # Local desktop app
```

## Architecture

### Component System

Rio uses a dual implementation pattern for components:

**Python Side** (`/rio/components/`):
- Component class definitions with state/logic
- Observable properties that auto-trigger re-renders on change
- `build()` method for high-level components (compose from other components)
- `_custom_serialize_()` for sending state to frontend
- `_on_message_()` for handling frontend events

**TypeScript Side** (`/frontend/code/components/`):
- `ComponentBase` subclasses that create/update DOM elements
- `createElement()`: Build initial DOM structure
- `updateElement(deltaState)`: Apply state changes from Python
- Event handlers that send messages back to Python

**Component Hierarchy**:
```
Component (metaclass: ComponentMeta)
├── FundamentalComponent (maps to TypeScript/HTML, low-level)
│   └── Examples: Button, Text, ListView, Image
└── User Components (high-level, composed via build())
    └── Examples: Custom business logic components
```

### Observable Property System

Rio uses `ComponentMeta` metaclass to transform component classes into observable dataclasses:
- Properties automatically track dependencies
- Reading a property during `build()` registers a dependency
- Changing a property triggers rebuild of dependent components
- State synchronization happens automatically between Python ↔ TypeScript

### Session Management

- Each client connection = one `Session` instance (`rio/session.py`)
- Session maintains: component tree, active page, user settings, timezone, window dimensions
- Components created within session context get auto-registered
- WebSocket communication for real-time updates

## Project Structure

### Python Backend
- `/rio/components/` - Built-in component implementations
- `/rio/app.py` - Core `App` class and application setup
- `/rio/session.py` - Session state and lifecycle management
- `/rio/cli/` - Command-line interface (rio new, rio run, etc.)
- `/rio/observables/` - Observable property system and state tracking
- `/rio/transports/` - WebSocket and HTTP transport layers
- `/rio/component_meta.py` - Metaclass for component creation

### TypeScript Frontend
- `/frontend/code/components/` - Component rendering implementations
- `/frontend/code/rpc.ts` - RPC communication with Python backend
- `/frontend/code/componentManagement.ts` - Component lifecycle and tree management
- `/frontend/css/components/` - Component-specific SCSS styles
- `/frontend/index.html` - Frontend entry point

### Build System
- `/vite.config.mjs` - Vite build configuration
- Output: `/rio/frontend files/` (auto-generated, included in wheel)
- Build process compiles TypeScript + SCSS → bundled assets

### Testing
- `/tests/test_components.py` - Component behavior tests
- `/tests/test_frontend/` - Browser-based integration tests
- `/tests/test_cli/` - CLI command tests
- `/tests/test_observables.py` - State management tests

### Scripts
- `/scripts/build_icon_set.py` - Build icon sets from SVGs
- `/scripts/code_coverage.py` - Generate coverage reports
- `/scripts/publish.py` - Release/publishing automation
- `/scripts/generate_stubs.py` - Type stub generation

## Development Workflow

### Adding New Built-in Components

1. Create Python component in `/rio/components/my_component.py`
2. Create TypeScript component in `/frontend/code/components/myComponent.ts`
3. Add SCSS styles in `/frontend/css/components/myComponent.scss`
4. Export from `/rio/components/__init__.py`
5. Add tests in `/tests/test_components.py`
6. Build frontend: `npm run dev-build`

### Making Frontend Changes

Frontend changes require rebuilding since TypeScript compiles to bundled assets:
```bash
# After editing .ts or .scss files
npm run dev-build
```

### Component Lifecycle

When a component is instantiated (`ComponentMeta.__call__`):
1. Session injection: `component._session_ = currently_building_session`
2. ID assignment: `component._id_ = session._next_free_component_id`
3. Registration in session's component registry
4. Property tracking setup for dependency management
5. Key registration for component reuse/reconciliation

## Code Conventions

### Naming
- **Event handlers**: Present tense (`on_change`, `on_press`, not `on_changed`)
- **Boolean properties**: Affirmative (`is_visible`, not `is_hidden`)
- **Dictionaries**: `keys_to_values` pattern (e.g., `ids_to_instances`)
- **Units**: SI base units (seconds, not milliseconds) unless unit in name
- **Python**: `snake_case` for variables/functions, `CamelCase` for classes
- **TypeScript**: `camelCase` for variables/functions, `UpperCamelCase` for classes
- **Files**: `snake_case` (Python), `camelCase` (TypeScript)

### Imports
Prefer importing modules, not values:
```python
# Good
import traceback
traceback.print_exc()

# Avoid
from traceback import print_exc
```

Exceptions for common imports:
```python
from __future__ import annotations  # Always first

from datetime import datetime, timezone, timedelta
from pathlib import Path

import typing as t
import typing_extensions as te
import numpy as np
import pandas as pd
```

### Type Hints
- Use type hints extensively (helps users, type checkers, and IDE autocomplete)
- Rio is fully type-safe, which is a core feature
- Use `typing` module with `t.` alias
- Use `typing_extensions as te` for newer features

## Testing Guidelines

- Tests must work with built frontend assets (run `npm run dev-build` if frontend tests fail)
- Component tests focus on state changes and user interactions
- Use `uv run pytest` to run tests in proper environment
- Coverage reporting via `uv run scripts/code_coverage.py`
- Frontend tests require browser setup (Playwright)

## Pre-commit Hooks

Automatically run on commit:
- Ruff: Python linting and formatting
- Prettier: TypeScript/CSS/JSON formatting

## Common Pitfalls

### Frontend Development
- Always rebuild after TypeScript changes (`npm run dev-build`)
- Component state sync: Ensure `_custom_serialize_()` matches TypeScript expectations
- Each FundamentalComponent needs unique class name and `_unique_id_`

### Python Development
- Don't bypass observable property system - use normal attribute assignment
- Components must be created within session context
- Understand `ComponentMeta` instantiation process for advanced work

### Build Process
- Frontend assets are compiled into `/rio/frontend files/` and included in Python wheel
- Changes to `/frontend/` don't take effect until rebuild
- Production builds use minification and compression
