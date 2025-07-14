# Rio Framework - Developer Guide for Contributors

## Overview
Rio is a Python-first web framework with a hybrid architecture: Python backend for component logic/state management + TypeScript frontend for DOM rendering. This guide is for contributors developing the Rio framework itself.

## Architecture for Framework Contributors

### Dual Implementation Pattern
- **Python side**: Component definitions, logic, server communication (`/rio/components/`)
- **TypeScript side**: DOM rendering, event handling, client interactions (`/frontend/code/components/`)
- **Communication**: RPC calls and data models via WebSocket/HTTP
- **Build process**: TypeScript compiles to `/rio/frontend files/`, included in Python wheel

### Component Implementation Hierarchy
```
Component (Abstract Base, ComponentMeta)
├── FundamentalComponent (Maps to TypeScript/HTML)
│   ├── Button → _ButtonInternal (TypeScript)
│   ├── ListView → ListView (TypeScript)
│   └── Other built-in components
└── User Components (High-level, composed via build())
```

### Key Internal Systems
- **ComponentMeta**: Metaclass transforming classes into observable dataclasses
- **Observable Properties**: `ComponentProperty` with dependency tracking
- **State Synchronization**: Python ↔ TypeScript via `_custom_serialize_()` and `_on_message_()`
- **Reconciliation**: Component tree diffing and reuse via `_weak_builder_` and `key_to_component`

## Development Environment Setup

### Initial Setup (Required Order)
```bash
# 1. Install Python dependencies
uv sync --all-extras

# 2. Install frontend dependencies  
npm install

# 3. Build frontend (REQUIRED before first use)
uv run scripts/build.py

# 4. Setup pre-commit hooks
python -m pre_commit install
```

### Frontend Build System
```bash
# Development build (default)
uv run scripts/build.py

# Production build (for releases)
uv run scripts/build.py --release
```

**When to rebuild frontend:**
- After any TypeScript/SCSS changes in `/frontend/`
- Before testing (some tests require built assets)
- Before releases (production build required)

### Project Structure
- `/rio/components/` - Python component implementations
- `/frontend/code/components/` - TypeScript component implementations  
- `/frontend/css/components/` - Component-specific SCSS files
- `/rio/frontend files/` - Compiled frontend assets (generated)
- `/scripts/` - Build and development tools

## Component Development Patterns

### Creating New FundamentalComponents
```python
# Python side (rio/components/my_component.py)
class MyComponent(FundamentalComponent):
    text: str = ""
    
    def build_javascript_source(self) -> str:
        return JAVASCRIPT_SOURCE_TEMPLATE % {
            'js_wrapper_class_name': 'MyComponentWrapper',
            'js_user_class_name': 'MyComponent',
            'cls_unique_id': self._unique_id_,
        }
    
    def _custom_serialize_(self) -> JsonDoc:
        return {'text': self.text}
    
    async def _on_message_(self, message: JsonDoc) -> None:
        # Handle frontend messages
        pass
```

```typescript
// TypeScript side (frontend/code/components/myComponent.ts)
class MyComponent extends ComponentBase {
    createElement(): HTMLElement {
        return document.createElement('div');
    }
    
    updateElement(deltaState: any): void {
        if (deltaState.text !== undefined) {
            this.element.textContent = deltaState.text;
        }
    }
}
```

### Component Lifecycle Management
```python
# Component instantiation (ComponentMeta.__call__)
1. Session injection: component._session_ = global_state.currently_building_session
2. ID assignment: component._id_ = session._next_free_component_id
3. Registration: session._newly_created_components.add(component)
4. Property tracking: component._properties_set_by_creator_
5. Key registration: global_state.key_to_component[key] = component
```

### Observable Property System
```python
# Properties automatically track access and changes
@dataclasses.dataclass
class MyComponent(Component):
    count: int = 0  # Becomes ComponentProperty
    
    def build(self) -> Component:
        # Reading self.count registers dependency
        # Changing self.count triggers rebuild
        return Text(f"Count: {self.count}")
```

## Testing Framework Contributors

### Test Organization
```bash
# Python backend tests
uv run pytest tests/

# Frontend integration tests (requires browser)
uv run pytest tests/test_frontend/

# Coverage reporting
uv run scripts/code_coverage.py
```

### Test Categories
- **Component tests**: `tests/test_components.py` - Component behavior
- **Observable tests**: `tests/test_observables.py` - State management
- **Frontend tests**: `tests/test_frontend/` - Browser-based testing
- **CLI tests**: `tests/test_cli/` - Command-line interface

## Icon System Development
```bash
# Build icon sets from raw SVGs
uv run scripts/build_icon_set.py

# Icon locations:
# - /raw_icons/ - Source SVG files
# - /thirdparty/bootstrap/icons/ - Bootstrap icons
# - Output: .tar.xz archives → /rio/assets/icon_sets/
```

## Code Quality and Conventions

### Code Standards
```bash
# Python linting and formatting
python -m ruff check .
python -m ruff format .

# TypeScript formatting
npx prettier --write frontend/

# Pre-commit hooks (automatic)
pre-commit run --all-files
```

### Import Patterns
```python
from __future__ import annotations  # Always first
import dataclasses
import typing as t
import rio
from .. import global_state, inspection  # Relative imports
```

### Type Annotations
- Heavy use of `typing` module with `t.` aliases
- All public APIs fully type-annotated
- Use `@t.final` for non-subclassable classes
- `typing_extensions` for newer features

## Common Development Tasks

### Adding New Built-in Components
1. Create Python component in `/rio/components/`
2. Create TypeScript component in `/frontend/code/components/`
3. Add SCSS styles in `/frontend/css/components/`
4. Update `/rio/components/__init__.py` exports
5. Add tests in `/tests/test_components.py`
6. Build frontend: `uv run scripts/build.py`

### Debugging Component Issues
- Use `rio.global_state` for session inspection
- Check `session._changed_attributes` for state changes
- Frontend: Browser DevTools + component tree visualization
- Backend: Python debugger with component lifecycle hooks


## Integration Points for Contributors

### Python-TypeScript Bridge
- State serialization: `_custom_serialize_()` → TypeScript
- Event handling: TypeScript → `_on_message_()` → Python
- DOM updates: Delta state application in TypeScript

### Session Management
- Session state in `rio/session.py`
- Component registration and lifecycle
- WebSocket communication via `rio/transports/`


## Common Pitfalls for Contributors

### Frontend Development
- **Always rebuild after TypeScript changes**: `uv run scripts/build.py`
- **Component registration**: Each FundamentalComponent needs unique `_unique_id_`
- **State synchronization**: Ensure `_custom_serialize_()` matches TypeScript expectations
- **CSS organization**: Component styles go in `/frontend/css/components/`

### Python Development
- **Observable properties**: Don't bypass the property system - use attribute assignment
- **Component lifecycle**: Understand `ComponentMeta` instantiation process
- **Session management**: Components must be created within session context
- **Import organization**: Use relative imports within Rio codebase

### Testing
- **Frontend tests**: Require built assets and browser setup
- **Component tests**: Focus on state changes and user interactions
- **Coverage**: Use `scripts/code_coverage.py` for comprehensive reporting
- **Mock dependencies**: Isolate components from external systems

