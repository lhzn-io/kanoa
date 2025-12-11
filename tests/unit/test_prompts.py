from kanoa.utils.prompts import (
    DEFAULT_PROMPTS,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_USER_PROMPT,
    PromptTemplates,
)


def test_prompts_exist() -> None:
    assert "{kb_context}" in DEFAULT_SYSTEM_PROMPT
    assert "{context_block}" in DEFAULT_USER_PROMPT
    assert "{focus_block}" in DEFAULT_USER_PROMPT


def test_prompt_templates_class() -> None:
    """Test PromptTemplates dataclass."""
    templates = PromptTemplates()

    # Check default templates exist
    assert templates.system_prompt
    assert templates.user_prompt
    assert "{kb_context}" in templates.system_prompt
    assert "{context_block}" in templates.user_prompt
    assert "{focus_block}" in templates.user_prompt


def test_default_prompts_instance() -> None:
    """Test DEFAULT_PROMPTS instance."""
    assert DEFAULT_PROMPTS.system_prompt == DEFAULT_SYSTEM_PROMPT
    assert DEFAULT_PROMPTS.user_prompt == DEFAULT_USER_PROMPT


def test_prompt_templates_get_methods() -> None:
    """Test get_system_prompt and get_user_prompt methods."""
    templates = PromptTemplates()

    # Test without backend (should return defaults)
    assert templates.get_system_prompt() == templates.system_prompt
    assert templates.get_user_prompt() == templates.user_prompt

    # Test with unknown backend (should return defaults)
    assert templates.get_system_prompt("unknown") == templates.system_prompt
    assert templates.get_user_prompt("unknown") == templates.user_prompt


def test_prompt_templates_backend_overrides() -> None:
    """Test backend-specific prompt overrides."""
    custom_system = "You are an inertial navigation specialist..."
    custom_user = "Analyze this sensor data..."

    templates = PromptTemplates(
        backend_overrides={
            "gemini": {
                "system_prompt": custom_system,
                "user_prompt": custom_user,
            }
        }
    )

    # Check gemini backend gets custom prompts
    assert templates.get_system_prompt("gemini") == custom_system
    assert templates.get_user_prompt("gemini") == custom_user

    # Check other backends get defaults
    assert templates.get_system_prompt("claude") == templates.system_prompt
    assert templates.get_user_prompt("claude") == templates.user_prompt


def test_prompt_templates_customization() -> None:
    """Test custom prompt templates."""
    custom_system = "You are a specialized analyst..."
    custom_user = "Provide detailed analysis..."

    templates = PromptTemplates(
        system_prompt=custom_system,
        user_prompt=custom_user,
    )

    assert templates.system_prompt == custom_system
    assert templates.user_prompt == custom_user
    assert templates.get_system_prompt() == custom_system
    assert templates.get_user_prompt() == custom_user
