import introspection
import pytest

import rio

# Sometimes components need a custom `__init__` method, and it's easy to
# overlook mutable default values when you turn the type annotations into
# constructor parameters. This can lead to components sharing state ACROSS
# SESSIONS, which is REALLY REALLY bad. Make sure there are no constructors with
# mutable default arguments.
all_components = list(introspection.get_subclasses(rio.Component))


@pytest.mark.parametrize(
    "cls", all_components, ids=[cls.__name__ for cls in all_components]
)
def test_constructor_has_no_mutable_defaults(cls: type):
    constructor_signature = introspection.signature(cls)
    params_with_mutable_defaults = [
        parameter.name
        for parameter in constructor_signature.parameter_list
        if isinstance(parameter.default, (list, dict, set))
    ]

    assert not params_with_mutable_defaults, (
        f"{cls.__name__} has parameters with mutable defaults: {params_with_mutable_defaults}"
    )
