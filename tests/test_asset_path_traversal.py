from pathlib import Path

import fastapi.testclient
import pytest

import rio


@pytest.fixture
def client(tmp_path: Path) -> fastapi.testclient.TestClient:
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "public.txt").write_text("public")
    (tmp_path / "secret.txt").write_text("secret")

    app = rio.App(build=rio.Spacer, assets_dir=assets_dir)
    fastapi_app = app._as_fastapi(
        debug_mode=False,
        running_in_window=False,
        internal_on_app_start=None,
        base_url=None,
    )
    return fastapi.testclient.TestClient(fastapi_app)


def test_serves_assets(client: fastapi.testclient.TestClient) -> None:
    response = client.get("/rio/assets/user/public.txt")
    assert response.status_code == 200
    assert response.text == "public"


@pytest.mark.parametrize(
    "path",
    [
        "%2e%2e/secret.txt",
        "..%2fsecret.txt",
        "..%5csecret.txt",
        "%2e%2e%2fsecret.txt",
    ],
)
def test_rejects_path_traversal(
    client: fastapi.testclient.TestClient,
    path: str,
) -> None:
    response = client.get(f"/rio/assets/user/{path}")
    assert response.status_code == 404
    assert "secret" not in response.text
