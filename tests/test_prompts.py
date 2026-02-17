"""Tests for claw2immich/prompts.py"""


def test_prompts_module_available():
    """Test that prompts module can be imported."""
    from claw2immich import prompts
    
    assert prompts is not None


def test_register_prompts_and_resources():
    """Test that register_prompts_and_resources is callable."""
    from claw2immich.prompts import register_prompts_and_resources
    
    # Test that the function exists and is callable
    assert callable(register_prompts_and_resources)


def test_load_usage_guide():
    """Test that _load_usage_guide can be imported."""
    from claw2immich.prompts import _load_usage_guide
    
    # Test that the function exists
    assert callable(_load_usage_guide)
