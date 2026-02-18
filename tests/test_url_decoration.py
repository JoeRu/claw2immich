"""Tests for URL decoration functions in claw2immich/tooling.py"""
import pytest


def test_should_decorate_response_asset():
    """Test _should_decorate_response detects asset endpoints."""
    from claw2immich.tooling import _should_decorate_response
    
    result, url_type = _should_decorate_response("GET", "/assets/{id}")
    assert result is True
    assert url_type == "asset"


def test_should_decorate_response_album():
    """Test _should_decorate_response detects album endpoints."""
    from claw2immich.tooling import _should_decorate_response
    
    result, url_type = _should_decorate_response("GET", "/albums/{id}")
    assert result is True
    assert url_type == "album"


def test_should_decorate_response_person():
    """Test _should_decorate_response detects person endpoints."""
    from claw2immich.tooling import _should_decorate_response
    
    result, url_type = _should_decorate_response("GET", "/people/{id}")
    assert result is True
    assert url_type == "person"


def test_should_decorate_response_place():
    """Test _should_decorate_response detects place endpoints."""
    from claw2immich.tooling import _should_decorate_response
    
    result, url_type = _should_decorate_response("GET", "/places/{id}")
    assert result is True
    assert url_type == "place"


def test_should_decorate_response_no_match():
    """Test _should_decorate_response ignores non-matching endpoints."""
    from claw2immich.tooling import _should_decorate_response
    
    result, url_type = _should_decorate_response("GET", "/server/version")
    assert result is False
    assert url_type is None


def test_should_decorate_response_post_not_decorated():
    """Test _should_decorate_response only decorates GET methods."""
    from claw2immich.tooling import _should_decorate_response
    
    result, url_type = _should_decorate_response("POST", "/assets/{id}")
    assert result is False
    assert url_type is None


def test_extract_single_id_with_id_field():
    """Test _extract_single_id extracts id field."""
    from claw2immich.tooling import _extract_single_id
    
    data = {"id": "abc-123", "name": "Test Asset"}
    result = _extract_single_id(data)
    assert result == "abc-123"


def test_extract_single_id_with_albumid_field():
    """Test _extract_single_id extracts albumId field."""
    from claw2immich.tooling import _extract_single_id
    
    data = {"albumId": "album-456", "albumName": "My Album"}
    result = _extract_single_id(data)
    assert result == "album-456"


def test_extract_single_id_with_personid_field():
    """Test _extract_single_id extracts personId field."""
    from claw2immich.tooling import _extract_single_id
    
    data = {"personId": "person-789", "name": "John"}
    result = _extract_single_id(data)
    assert result == "person-789"


def test_extract_single_id_with_placeid_field():
    """Test _extract_single_id extracts placeId field."""
    from claw2immich.tooling import _extract_single_id
    
    data = {"placeId": "place-999", "name": "New York"}
    result = _extract_single_id(data)
    assert result == "place-999"


def test_extract_single_id_no_id():
    """Test _extract_single_id returns None when no ID found."""
    from claw2immich.tooling import _extract_single_id
    
    data = {"name": "Test", "description": "No ID here"}
    result = _extract_single_id(data)
    assert result is None


def test_extract_single_id_not_dict():
    """Test _extract_single_id returns None for non-dict input."""
    from claw2immich.tooling import _extract_single_id
    
    result = _extract_single_id("not a dict")
    assert result is None


def test_extract_single_id_empty_dict():
    """Test _extract_single_id returns None for empty dict."""
    from claw2immich.tooling import _extract_single_id
    
    result = _extract_single_id({})
    assert result is None


def test_decorate_response_asset():
    """Test _decorate_response adds web_url for asset."""
    from claw2immich.tooling import _decorate_response
    
    response = {"id": "asset-123", "name": "My Photo"}
    decorated = _decorate_response(response, "https://immich.example.com", "asset")
    
    assert "web_url" in decorated
    assert decorated["web_url"] == "https://immich.example.com/photos/asset-123"


def test_decorate_response_album():
    """Test _decorate_response adds web_url for album."""
    from claw2immich.tooling import _decorate_response
    
    response = {"albumId": "album-456", "albumName": "My Album"}
    decorated = _decorate_response(response, "https://immich.example.com", "album")
    
    assert "web_url" in decorated
    assert decorated["web_url"] == "https://immich.example.com/albums/album-456"


def test_decorate_response_person():
    """Test _decorate_response adds web_url for person."""
    from claw2immich.tooling import _decorate_response
    
    response = {"personId": "person-789", "name": "John"}
    decorated = _decorate_response(response, "https://immich.example.com", "person")
    
    assert "web_url" in decorated
    assert decorated["web_url"] == "https://immich.example.com/people/person-789"


def test_decorate_response_place():
    """Test _decorate_response adds web_url for place."""
    from claw2immich.tooling import _decorate_response
    
    response = {"placeId": "place-999", "name": "New York"}
    decorated = _decorate_response(response, "https://immich.example.com", "place")
    
    assert "web_url" in decorated
    assert decorated["web_url"] == "https://immich.example.com/explore?places=place-999"


def test_decorate_response_no_domain():
    """Test _decorate_response returns unchanged response when no domain."""
    from claw2immich.tooling import _decorate_response
    
    response = {"id": "asset-123", "name": "My Photo"}
    decorated = _decorate_response(response, None, "asset")
    
    assert "web_url" not in decorated
    assert decorated == response


def test_decorate_response_not_dict():
    """Test _decorate_response returns unchanged response for non-dict."""
    from claw2immich.tooling import _decorate_response
    
    response = "string response"
    decorated = _decorate_response(response, "https://immich.example.com", "asset")
    
    assert decorated == response


def test_decorate_response_no_id():
    """Test _decorate_response returns unchanged response when no ID."""
    from claw2immich.tooling import _decorate_response
    
    response = {"name": "No ID here", "description": "Test"}
    decorated = _decorate_response(response, "https://immich.example.com", "asset")
    
    assert "web_url" not in decorated
    assert decorated == response


def test_decorate_response_existing_web_url():
    """Test _decorate_response does not overwrite existing web_url."""
    from claw2immich.tooling import _decorate_response
    
    response = {"id": "asset-123", "web_url": "https://custom.url"}
    decorated = _decorate_response(response, "https://immich.example.com", "asset")
    
    # Should not overwrite existing web_url
    assert decorated["web_url"] == "https://custom.url"


def test_decorate_response_http_domain():
    """Test _decorate_response works with HTTP domain."""
    from claw2immich.tooling import _decorate_response
    
    response = {"id": "asset-123"}
    decorated = _decorate_response(response, "http://localhost:2283", "asset")
    
    assert "web_url" in decorated
    assert decorated["web_url"] == "http://localhost:2283/photos/asset-123"

