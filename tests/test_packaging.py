"""Tests for packaging metadata and release workflow assumptions."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_wheel_force_includes_are_present_in_sdist_includes():
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text()
    assert '"release_test_matrix.md" = "release_test_matrix.md"' in pyproject
    assert '"/release_test_matrix.md"' in pyproject


def test_publish_workflow_builds_once_then_reuses_artifact():
    workflow = (PROJECT_ROOT / ".github/workflows/publish.yml").read_text()
    assert workflow.count("run: uv build") == 1
    assert "actions/download-artifact" in workflow
    assert "packages-dir: dist/" in workflow
