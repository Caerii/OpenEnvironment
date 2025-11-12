from server.semantic.prompts.react import build_system_prompt, build_user_prompt


def test_build_system_prompt_injects_context():
    scene_summary = "Features: mountain ×2"
    recent_actions = "• create dramatic mountains"
    prompt = build_system_prompt(scene_summary, recent_actions, ["dramatic", "rugged"])
    assert scene_summary in prompt
    assert recent_actions in prompt
    assert "narrative" in prompt.lower()


def test_build_user_prompt_injects_counts():
    prompt = build_user_prompt(
        "create dramatic mountains",
        "Features: mountain ×2",
        "• create dramatic mountains",
        ["dramatic"],
        feature_count=3,
        entity_count=1,
        seed=42,
    )
    assert "features=3" in prompt
    assert "dramatic" in prompt
    assert "seed=42" in prompt
