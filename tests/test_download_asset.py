from unittest.mock import patch

from claw2immich.tooling import download_asset


def test_download_asset_default_base64() -> None:
    with patch(
        "claw2immich.tooling._request_bytes",
        return_value=(
            b"abc",
            {
                "content-type": "image/jpeg",
                "content-disposition": 'attachment; filename="image.jpg"',
            },
        ),
    ):
        result = download_asset("asset-1")

    assert result["asset_id"] == "asset-1"
    assert result["output"] == "base64"
    assert result["content_type"] == "image/jpeg"
    assert result["size_bytes"] == 3
    assert result["filename"] == "image.jpg"
    assert result["data"] == "YWJj"


def test_download_asset_binary_mode() -> None:
    with patch(
        "claw2immich.tooling._request_bytes",
        return_value=(b"\x00\x01\x02", {"content-type": "application/octet-stream"}),
    ):
        result = download_asset("asset-2", output="binary")

    assert result["asset_id"] == "asset-2"
    assert result["output"] == "base64"
    assert result["requested_output"] == "binary"
    assert result["encoding"] == "base64"
    assert result["size_bytes"] == 3
    assert result["data"] == "AAEC"
    assert "warning" in result


def test_download_asset_rejects_invalid_output() -> None:
    result = download_asset("asset-3", output="json")
    assert "error" in result
    assert "base64" in result["error"]


def test_download_asset_immich_link_delivery_mode() -> None:
    """immich_link falls back to base_url when no external domain is configured."""
    with patch(
        "claw2immich.tooling.get_download_asset_delivery_mode",
        return_value="immich_link",
    ), patch(
        "claw2immich.tooling.get_external_domain",
        return_value=None,
    ), patch(
        "claw2immich.tooling._get_config",
        return_value={
            "base_url": "https://immich.example.com",
            "api_key": "test",
            "api_token": "",
        },
    ):
        result = download_asset("asset-link")

    assert result["asset_id"] == "asset-link"
    assert result["delivery_mode"] == "immich_link"
    assert result["requires_auth"] is True
    assert result["download_url"] == "https://immich.example.com/api/assets/asset-link/original"


def test_download_asset_immich_link_prefers_external_domain() -> None:
    """immich_link uses the external domain when it is configured."""
    with patch(
        "claw2immich.tooling.get_download_asset_delivery_mode",
        return_value="immich_link",
    ), patch(
        "claw2immich.tooling.get_external_domain",
        return_value="https://photos.mydomain.com",
    ), patch(
        "claw2immich.tooling._get_config",
        return_value={
            "base_url": "http://immich:2283",
            "api_key": "test",
            "api_token": "",
        },
    ):
        result = download_asset("asset-ext")

    assert result["asset_id"] == "asset-ext"
    assert result["delivery_mode"] == "immich_link"
    assert result["download_url"] == "https://photos.mydomain.com/api/assets/asset-ext/original"
