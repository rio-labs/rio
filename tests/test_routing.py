import pytest

import rio.app_server


class FakeComponent(rio.Component):
    pass


class FakeSession:
    def __init__(self) -> None:
        self._base_url = rio.URL("http://foo.com")


PAGES = [
    rio.ComponentPage(
        name="Home",
        url_segment="",
        build=FakeComponent,
    ),
    rio.ComponentPage(
        name="Page 1",
        url_segment="page-1",
        build=FakeComponent,
    ),
    rio.ComponentPage(
        name="Page 2",
        url_segment="page-2",
        build=FakeComponent,
    ),
    rio.ComponentPage(
        name="Guard to Page 1",
        url_segment="guard-to-page-1",
        build=FakeComponent,
        guard=lambda _: "page-1",
    ),
    rio.ComponentPage(
        name="Guard to Cycle 1",
        url_segment="guard-to-cycle-1",
        build=FakeComponent,
        guard=lambda _: "guard-to-cycle-2",
    ),
    rio.ComponentPage(
        name="Guard to Cycle 2",
        url_segment="guard-to-cycle-2",
        build=FakeComponent,
        guard=lambda _: "guard-to-cycle-1",
    ),
    rio.Redirect(
        url_segment="redirect-to-page-1",
        target="page-1",
    ),
    rio.Redirect(
        url_segment="redirect-to-cycle-1",
        target="guard-to-cycle-2",
    ),
    rio.Redirect(
        url_segment="redirect-to-cycle-2",
        target="guard-to-cycle-1",
    ),
]


@pytest.mark.parametrize(
    "relative_url_before_redirects,relative_url_after_redirects_should",
    [
        # No redirects
        (
            "/page-1",
            "/page-1",
        ),
        (
            "/page-1?foo=bar",
            "/page-1?foo=bar",
        ),
        (
            "/page-1#foo",
            "/page-1#foo",
        ),
        # Redirects by guard
        (
            "/guard-to-page-1",
            "/page-1",
        ),
        (
            "/guard-to-page-1?foo=bar",
            "/page-1?foo=bar",
        ),
        (
            "/guard-to-page-1#foo",
            "/page-1#foo",
        ),
        # Redirects by `rio.Redirect`
        (
            "/redirect-to-page-1",
            "/page-1",
        ),
        (
            "/redirect-to-page-1?foo=bar",
            "/page-1?foo=bar",
        ),
        (
            "/redirect-to-page-1#foo",
            "/page-1#foo",
        ),
        # No such page
        (
            "/non-existent-page",
            "/non-existent-page",
        ),
        (
            "/non-existent-page?foo=bar",
            "/non-existent-page?foo=bar",
        ),
        (
            "/non-existent-page#foo",
            "/non-existent-page#foo",
        ),
        # TODO: Add tests for URLs with Unicode characters & escaped/unescaped
        # URLs
    ],
)
def test_redirects(
    relative_url_before_redirects: str,
    relative_url_after_redirects_should: str,
) -> None:
    # Create a fake session. It contains everything used by the routing system.
    # fake_session = t.cast(rio.Session, FakeSession())
    #
    # Apps only initialize their pages later, so the parameter here has no
    # effect. They are overwritten manually instead
    app = rio.App(
        pages=(),
    )
    app.pages = tuple(PAGES)

    fake_app_server = object.__new__(rio.app_server.FastapiServer)
    fake_app_server.app = app

    fake_session = object.__new__(rio.Session)
    fake_session._base_url = rio.URL("http://foo.com")
    fake_session._active_page_url = fake_session._base_url
    fake_session._app_server = fake_app_server

    # Determine the final URL
    active_pages, absolute_url_after_redirects_is = (
        rio.routing.check_page_guards(
            fake_session,
            fake_session._base_url.join(rio.URL(relative_url_before_redirects)),
        )
    )

    # Verify the final URL
    absolute_url_after_redirects_should = fake_session._base_url.join(
        rio.URL(relative_url_after_redirects_should)
    )

    assert (
        absolute_url_after_redirects_is == absolute_url_after_redirects_should
    )


test_redirects(
    "/guard-to-page-1",
    "/page-1",
)
