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
    assert result["output"] == "binary"
    assert result["size_bytes"] == 3
    assert result["data"] == b"\x00\x01\x02"


def test_download_asset_rejects_invalid_output() -> None:
    result = download_asset("asset-3", output="json")
    assert "error" in result
    assert "base64" in result["error"]
