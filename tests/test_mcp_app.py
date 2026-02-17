"""Tests for claw2immich/mcp_app.py"""
from unittest.mock import patch


def test_resolve_external_domain_success():
    """Test _resolve_external_domain with successful API response."""
    from claw2immich.mcp_app import _resolve_external_domain
    
    mock_response = {"externalDomain": "immich.example.com"}
    
    with patch("claw2immich.mcp_app._request", return_value=mock_response):
        domain = _resolve_external_domain()
        assert domain == "immich.example.com"


def test_resolve_external_domain_alternative_field():
    """Test _resolve_external_domain with alternative field name."""
    from claw2immich.mcp_app import _resolve_external_domain
    
    mock_response = {"external_domain": "immich.example.com"}
    
    with patch("claw2immich.mcp_app._request", return_value=mock_response):
        domain = _resolve_external_domain()
        assert domain == "immich.example.com"


def test_resolve_external_domain_empty():
    """Test _resolve_external_domain with empty externalDomain."""
    from claw2immich.mcp_app import _resolve_external_domain
    
    mock_response = {"externalDomain": ""}
    
    with patch("claw2immich.mcp_app._request", return_value=mock_response):
        domain = _resolve_external_domain()
        assert domain is None


def test_resolve_external_domain_missing():
    """Test _resolve_external_domain when field is missing."""
    from claw2immich.mcp_app import _resolve_external_domain
    
    mock_response = {"someOtherField": "value"}
    
    with patch("claw2immich.mcp_app._request", return_value=mock_response):
        domain = _resolve_external_domain()
        assert domain is None


def test_resolve_external_domain_request_error():
    """Test _resolve_external_domain when _request raises exception."""
    from claw2immich.mcp_app import _resolve_external_domain
    from claw2immich.http_client import ImmichAPIError
    
    with patch("claw2immich.mcp_app._request", side_effect=ImmichAPIError("401", "Unauthorized")):
        domain = _resolve_external_domain()
        assert domain is None


def test_resolve_external_domain_non_dict_response():
    """Test _resolve_external_domain when response is not a dict."""
    from claw2immich.mcp_app import _resolve_external_domain
    
    with patch("claw2immich.mcp_app._request", return_value="not a dict"):
        domain = _resolve_external_domain()
        assert domain is None


def test_create_mcp():
    """Test create_mcp creates FastMCP instance."""
    from claw2immich.mcp_app import create_mcp
    from mcp.server.fastmcp import FastMCP
    
    with patch("claw2immich.mcp_app._resolve_external_domain", return_value=None):
        mcp = create_mcp()
        # Check that mcp is an instance of FastMCP
        assert isinstance(mcp, FastMCP)
        assert mcp.name == "claw2immich"


def test_run_validates_transport():
    """Test run() validates MCP_TRANSPORT."""
    from claw2immich.mcp_app import run
    import os
    
    os.environ["MCP_TRANSPORT"] = "invalid_transport"
    
    try:
        # Mock create_mcp and all its dependencies
        with patch("claw2immich.mcp_app.create_mcp") as mock_create:
            with patch("claw2immich.mcp_app.register_prompts_and_resources"):
                with patch("claw2immich.mcp_app._register_tools"):
                    mock_mcp = mock_create.return_value
                    with patch.object(mock_mcp, "run"):
                        try:
                            run()
                            assert False, "Should have raised ValueError"
                        except ValueError as e:
                            assert "MCP_TRANSPORT" in str(e)
    finally:
        os.environ.pop("MCP_TRANSPORT", None)
