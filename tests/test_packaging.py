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


def test_publish_workflow_publishes_when_github_release_is_published():
    workflow = (PROJECT_ROOT / ".github/workflows/publish.yml").read_text()
    assert "release:" in workflow
    assert "types: [created, published, released]" in workflow
    assert "release-context:" in workflow
    assert "tag_name: ${{ needs.release-context.outputs.tag_name }}" in workflow
    assert "ref: ${{ needs.release-context.outputs.tag_name }}" in workflow
    assert "name: dist-${{ needs.release-context.outputs.tag_name }}" in workflow
    assert "skip-existing: true" in workflow
