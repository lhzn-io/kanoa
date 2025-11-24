from kanoa.utils.prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT


def test_prompts_exist() -> None:
    assert "{kb_context}" in DEFAULT_SYSTEM_PROMPT
    assert "{context_block}" in DEFAULT_USER_PROMPT
    assert "{focus_block}" in DEFAULT_USER_PROMPT
