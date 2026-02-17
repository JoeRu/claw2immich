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


def test_all_prompts_have_descriptions():
    """Test that every prompt registered via register_prompts_and_resources has a non-empty description."""
    from claw2immich.prompts import register_prompts_and_resources

    registered_prompts = []

    class FakeMCP:
        def resource(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

        def prompt(self, *args, **kwargs):
            def decorator(fn):
                registered_prompts.append(kwargs)
                return fn
            return decorator

    fake = FakeMCP()
    register_prompts_and_resources(fake)

    assert len(registered_prompts) == 8, f"Expected 8 prompts, got {len(registered_prompts)}"
    for prompt_kwargs in registered_prompts:
        title = prompt_kwargs.get("title", "<no title>")
        desc = prompt_kwargs.get("description", "")
        assert desc, f"Prompt '{title}' has an empty description"
