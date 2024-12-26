import pytest

from tests.utils.layouting import cleanup, setup


# Putting this fixture here makes it run only once, even though we have a whole
# bunch of submodules.
@pytest.fixture(scope="module", autouse=True)
async def manage_server():
    await setup()
    yield
    await cleanup()
