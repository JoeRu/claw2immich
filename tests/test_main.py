import pytest

import main


def test_get_config_rejects_invalid_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMMICH_BASE_URL", "localhost:2283")
    with pytest.raises(ValueError):
        main._get_config()


def test_build_headers_requires_auth() -> None:
    config = {"base_url": "http://localhost:2283", "api_key": "", "api_token": ""}
    with pytest.raises(ValueError):
        main._build_headers(config, require_auth=True)


def test_build_headers_sets_api_key() -> None:
    config = {
        "base_url": "http://localhost:2283",
        "api_key": "key",
        "api_token": "",
    }
    headers = main._build_headers(config, require_auth=True)
    assert headers["x-api-key"] == "key"


def test_pagination_params_empty() -> None:
    assert main._pagination_params() is None


def test_pagination_params_values() -> None:
    params = main._pagination_params(page=1, size=10, order="desc")
    assert params == {"page": 1, "size": 10, "order": "desc"}


def test_openapi_summary_uses_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_spec() -> dict[str, object]:
        return {"info": {"title": "Immich", "version": "1"}, "paths": {"/a": {}, "/b": {}}}

    monkeypatch.setattr(main, "_fetch_openapi_spec", fake_spec)
    summary = main.openapi_summary()
    assert summary == {"title": "Immich", "version": "1", "path_count": 2}


def test_list_assets_calls_request(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_request(method: str, path: str, *, params=None, json_body=None, require_auth=False):
        captured["method"] = method
        captured["path"] = path
        captured["params"] = params
        captured["require_auth"] = require_auth
        return {"ok": True}

    monkeypatch.setattr(main, "_request", fake_request)
    result = main.list_assets(page=2, size=5, order="asc")
    assert result == {"ok": True}
    assert captured == {
        "method": "GET",
        "path": "/api/assets",
        "params": {"page": 2, "size": 5, "order": "asc"},
        "require_auth": True,
    }
