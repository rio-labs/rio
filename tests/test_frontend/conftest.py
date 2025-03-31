import pytest

from rio.testing import prepare_browser_client


# Somewhat counter-intuitively, `scope='module'` would be incorrect here. That
# would execute the fixture once for each submodule. Scoping it to the session
# instead does exactly what we want: It runs only once, and only if it's needed.
@pytest.fixture(scope="session", autouse=True)
@pytest.mark.async_timeout(60)  # Yes, fixtures can time out
async def manage_server():
    async with prepare_browser_client():
        yield
