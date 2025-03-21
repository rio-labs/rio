import enum
from datetime import datetime, timedelta

import introspection
import pytest

import rio


# Sometimes components need a custom `__init__` method, and it's easy to
# overlook mutable default values when you turn the type annotations into
# constructor parameters. This can lead to components sharing state ACROSS
# SESSIONS, which is REALLY REALLY bad. Make sure there are no constructors with
# mutable default arguments.
def is_mutable(value: object) -> bool:
    if value is None:
        return False

    if isinstance(
        value,
        (
            int,
            float,
            str,
            bytes,
            enum.Enum,
            datetime,
            timedelta,
            rio.Color,
            rio.SolidFill,
            rio.LinearGradientFill,
            rio.RadialGradientFill,
            rio.ImageFill,
            rio.utils.NotGiven,
        ),
    ):
        return False

    if value == ():
        return False

    return True


# We have to be careful here not to pick up any Components from test files. It
# makes vscode extremely confused and unable to run the tests.
all_components = [
    obj
    for obj in vars(rio).values()
    if isinstance(obj, type) and issubclass(obj, rio.Component)
]


@pytest.mark.parametrize(
    "cls", all_components, ids=[cls.__name__ for cls in all_components]
)
def test_constructor_has_no_mutable_defaults(cls: type):
    constructor_signature = introspection.signature(cls)
    params_with_mutable_defaults = [
        parameter.name
        for parameter in constructor_signature.parameter_list
        if parameter.has_default and is_mutable(parameter.default)
    ]

    assert not params_with_mutable_defaults, (
        f"{cls.__name__} has parameters with mutable defaults: {params_with_mutable_defaults}"
    )
