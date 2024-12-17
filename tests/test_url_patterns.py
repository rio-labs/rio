"""
Matches URL patterns to URLs, verifying that they match what they should.
"""

import typing as t

import pytest

import rio
from rio.url_pattern import UrlPattern


@pytest.mark.parametrize(
    "pattern, exception",
    [
        # Leading slash
        (
            "/foo",
            ValueError,
        ),
        # Trailing slash
        (
            "foo/",
            ValueError,
        ),
        # Just slashes
        (
            "/",
            ValueError,
        ),
        (
            "//",
            ValueError,
        ),
        # Multiple consecutive slashes
        (
            "foo//bar",
            ValueError,
        ),
        (
            "foo///bar",
            ValueError,
        ),
        # Unterminated path parameter
        (
            "foo/{param",
            ValueError,
        ),
        (
            "foo/{param:path",
            ValueError,
        ),
        (
            "foo/param}",
            ValueError,
        ),
        (
            "foo/param:path}",
            ValueError,
        ),
        # Invalid path parameter names
        (
            "{???}",
            ValueError,
        ),
        (
            "{param}/{param}",
            ValueError,
        ),
    ],
)
def test_invalid_url_pattern(
    pattern: str,
    exception: t.Type[Exception],
) -> None:
    """
    Tests that invalid patterns raise the correct exceptions.
    """
    with pytest.raises(exception):
        UrlPattern(pattern)


@pytest.mark.parametrize(
    "url, pattern_str, values_should, remaining_should",
    [
        # Empty match (as used in the home page)
        (
            "",
            "",
            {},
            "",
        ),
        # Single segment
        (
            "foo",
            "foo",
            {},
            "",
        ),
        (
            "foo/bar",
            "foo",
            {},
            "bar",
        ),
        # Multiple segments
        (
            "foo/bar/baz",
            "foo/bar",
            {},
            "baz",
        ),
        # Single path parameter
        (
            "foo",
            "{param}",
            {"param": "foo"},
            "",
        ),
        (
            "foo/bar",
            "{param}",
            {"param": "foo"},
            "bar",
        ),
        (
            "foo/bar",
            "foo/{param}",
            {"param": "bar"},
            "",
        ),
        (
            "foo/bar/baz",
            "foo/{param}",
            {"param": "bar"},
            "baz",
        ),
        (
            "foo/bar/baz/qux",
            "foo/{param}/baz",
            {"param": "bar"},
            "qux",
        ),
        # Multiple path parameters
        (
            "foo/bar/baz",
            "foo/{param1}/{param2}",
            {"param1": "bar", "param2": "baz"},
            "",
        ),
        (
            "foo/bar/baz/qux/quux",
            "foo/{param1}/baz/{param2}",
            {"param1": "bar", "param2": "qux"},
            "quux",
        ),
        # "Greedy" path parameter
        (
            "foo/bar/baz",
            "{param:path}",
            {"param": "foo/bar/baz"},
            "",
        ),
        (
            "foo/bar/baz",
            "foo/{param:path}",
            {"param": "bar/baz"},
            "",
        ),
        (
            "foo/bar/baz/qux/quux",
            "foo/{param1}/{param2:path}",
            {"param1": "bar", "param2": "baz/qux/quux"},
            "",
        ),
        (
            "foo/bar/baz/qux/quux",
            "{param:path}/qux",
            {"param": "foo/bar/baz"},
            "quux",
        ),
    ],
)
def test_url_pattern_should_match(
    url: str,
    pattern_str: str,
    values_should: dict[str, str],
    remaining_should: str,
) -> None:
    """
    Matches patterns to URLs and verifies that they match what they should. All
    provided patterns must match their URLs.
    """
    # Parse the pattern
    pattern_object = UrlPattern(pattern_str)

    # Match the URL
    did_match, values_are, remaining_are = pattern_object.match(url)

    # Verify that the URL matched
    assert did_match

    # Verify that the values are correct
    assert values_are == values_should

    # Verify that the remaining part of the URL is correct
    assert remaining_are == remaining_should


@pytest.mark.parametrize(
    "url, pattern_str",
    [
        (
            "foo",
            "",
        ),
        (
            "foo",
            "bar",
        ),
        (
            "foo",
            "foo/bar",
        ),
        (
            "users/foo",
            "user/{user_id}",
        ),
        (
            "",
            "{user_id}",
        ),
    ],
)
def test_url_pattern_should_not_match(
    url: str,
    pattern_str: str,
) -> None:
    """
    Matches patterns to URLs, verifying that they **don't** match.
    """
    # Parse the pattern
    pattern_object = UrlPattern(pattern_str)

    # Match the URL
    matched, _, _ = pattern_object.match(url)

    # Verify that the URL did not match
    assert not matched


def _build_empty() -> None:
    pass


def _build_and_verify_bool(value: bool = True) -> None:
    assert isinstance(value, bool)


def _build_and_verify_int(value: int = 123) -> None:
    assert isinstance(value, int) and not isinstance(value, (bool, float))


def _build_and_verify_float(value: float = 123.4) -> None:
    assert isinstance(value, float) and not isinstance(value, (bool, int))


def _build_and_verify_str(value: str = "default-value") -> None:
    assert isinstance(value, str)


@pytest.mark.parametrize(
    "url_str, pattern, build_function, kwargs_should",
    [
        (
            "foo/bar",
            "foo/bar",
            _build_empty,
            {},
        ),
        # Single path parameters of all types
        (
            "true",
            "{param}",
            _build_and_verify_bool,
            {"param": True},
        ),
        (
            "false",
            "{param}",
            _build_and_verify_bool,
            {"param": False},
        ),
        (
            "-1",
            "{param}",
            _build_and_verify_int,
            {"param": -1},
        ),
        (
            "0",
            "{param}",
            _build_and_verify_int,
            {"param": 0},
        ),
        (
            "1",
            "{param}",
            _build_and_verify_int,
            {"param": 1},
        ),
        (
            "-1.0",
            "{param}",
            _build_and_verify_float,
            {"param": -1.0},
        ),
        (
            "0.0",
            "{param}",
            _build_and_verify_float,
            {"param": 0.0},
        ),
        (
            "1.0",
            "{param}",
            _build_and_verify_float,
            {"param": 1.0},
        ),
        (
            "foo",
            "{param}",
            _build_and_verify_str,
            {"param": "foo"},
        ),
        # Query parameters
        (
            "foo?bar=baz",
            "foo",
            _build_and_verify_str,
            {"bar": "baz"},
        ),
        # Default fallback: Missing parameter
        #
        # The current implementation simply doesn't pass these values to the
        # build function, relying on Python to impute the default. Hence the
        # empty expected dictionaries.
        (
            "foo",
            "foo",
            _build_and_verify_bool,
            {},
        ),
        (
            "foo",
            "foo",
            _build_and_verify_int,
            {},
        ),
        (
            "foo",
            "foo",
            _build_and_verify_float,
            {},
        ),
        (
            "foo",
            "foo",
            _build_and_verify_str,
            {},
        ),
        # Default fallback: Invalid parameter
        (
            "foo?value=bar",
            "foo",
            _build_and_verify_bool,
            {},
        ),
        (
            "foo?value=bar",
            "foo",
            _build_and_verify_int,
            {},
        ),
        (
            "foo?value=bar",
            "foo",
            _build_and_verify_float,
            {},
        ),
        # TODO: Multiple parameters
    ],
)
def test_parse_url_kwargs(
    url_str: str,
    pattern: str,
    build_function: t.Callable[..., t.Any],
    kwargs_should: dict[str, object],
) -> None:
    """
    Matches URLs against patterns, ensuring the parameters are correctly
    extracted and parsed.
    """
    # Create a component page object
    page = rio.ComponentPage(
        name="Test Page",
        url_segment=pattern,
        build=build_function,
    )

    # Parse the provided URL
    url = rio.URL(url_str)
    did_match, raw_path_arguments, remaining_url = page._url_pattern.match(
        url.path,
    )

    assert did_match
    assert remaining_url == ""

    # Get the kwargs for the build function
    kwargs_are = page._url_params_to_kwargs(
        path_params=raw_path_arguments,
        query_params=url.query,
    )

    # Verify that the kwargs are correct
    assert kwargs_are == kwargs_should
