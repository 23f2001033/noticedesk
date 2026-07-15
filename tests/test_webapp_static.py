from pathlib import Path

import pytest

from app.main import WEBAPP_DIST
from app.services.webapp_static import resolve_webapp_file


def _make_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>spa shell</html>")
    assets = dist / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('hi')")
    return dist


def test_resolve_webapp_file_serves_existing_static_file(tmp_path: Path) -> None:
    dist = _make_dist(tmp_path)

    result = resolve_webapp_file("assets/app.js", dist)

    assert result == dist / "assets" / "app.js"


def test_resolve_webapp_file_falls_back_to_index_for_spa_route(tmp_path: Path) -> None:
    dist = _make_dist(tmp_path)

    result = resolve_webapp_file("login", dist)

    assert result == dist / "index.html"


def test_resolve_webapp_file_falls_back_to_index_for_root(tmp_path: Path) -> None:
    dist = _make_dist(tmp_path)

    result = resolve_webapp_file("", dist)

    assert result == dist / "index.html"


def test_resolve_webapp_file_blocks_path_traversal(tmp_path: Path) -> None:
    dist = _make_dist(tmp_path)
    (tmp_path / "secret.txt").write_text("top secret")

    result = resolve_webapp_file("../secret.txt", dist)

    assert result == dist / "index.html"


@pytest.mark.skipif(
    not WEBAPP_DIST.is_dir(), reason="webapp/dist not built (run `npm run build` in webapp/)"
)
def test_serve_webapp_returns_spa_shell_for_client_route(client) -> None:
    response = client.get("/login")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
