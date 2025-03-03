import pytest

from tests.utils.layouting import cleanup, setup


# Somewhat counter-intuitively, `scope='module'` would be incorrect here. That
# would execute the fixture once for each submodule. Scoping it to the session
# instead does exactly what we want: It runs only once, and only if it's needed.
@pytest.fixture(scope="session", autouse=True)
async def manage_server():
    await setup()
    yield
    await cleanup()


pytestmark = pytest.mark.async_timeout(15)
