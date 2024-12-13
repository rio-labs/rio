"""
Matches URL patterns to URLs, verifying that they match what they should.
"""

import pytest

from rio.url_pattern import UrlPattern


@pytest.mark.parametrize(
    "url, pattern_str, values_should, remaining_should",
    [
        (
            "/foo",
            "/foo",
            {},
            "",
        ),
        (
            "/foo/bar",
            "/foo",
            {},
            "/bar",
        ),
        (
            "/users/foo",
            "/users/{user_id}",
            {"user_id": "foo"},
            "",
        ),
        (
            "/users/foo/bar",
            "/users/{user_id}",
            {"user_id": "foo"},
            "/bar",
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
            "/foo",
            "/bar",
        ),
        (
            "/foo",
            "/foo/bar",
        ),
        (
            "/users/foo",
            "/user/{user_id}",
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
