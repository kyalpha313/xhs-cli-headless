from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_agent_skill_bundle_files_exist():
    required_paths = [
        "skills/SKILL.md",
        "skills/xhs-auth/SKILL.md",
        "skills/xhs-search/SKILL.md",
        "skills/xhs-read/SKILL.md",
        "skills/xhs-social/SKILL.md",
        "skills/xhs-ops/SKILL.md",
        "references/capability-boundary.md",
        "references/cli-command-map.md",
        "references/safety-rules.md",
        "scripts/run_xhs.py",
        "scripts/smoke_check.py",
    ]

    for relative_path in required_paths:
        assert (ROOT / relative_path).exists(), relative_path


def test_auth_skill_documents_session_recovery_flow():
    text = (ROOT / "skills/xhs-auth/SKILL.md").read_text(encoding="utf-8")

    assert "xhs auth doctor --json" in text
    assert "xhs login" in text
    assert "xhs auth import --file" in text
    assert "xhs auth import-fields --interactive" in text


def test_safety_rules_block_unstable_commands_by_default():
    text = (ROOT / "references/safety-rules.md").read_text(encoding="utf-8")

    for command in ["post", "delete", "favorites", "likes", "notifications", "sub-comments"]:
        assert command in text


def test_project_version_is_086():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'version = "0.8.6"' in pyproject
