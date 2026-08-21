from pathlib import Path


def test_ci_checks_package_and_source_and_installed_cli_contracts():
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "python -m pytest -q" in workflow
    assert "python -m build" in workflow
    assert "python -m twine check dist/*" in workflow
    assert workflow.count("chatgame --version") >= 2
    assert workflow.count("chatgame --tree\n") >= 2
    assert workflow.count("chatgame --tree-brief") >= 2


def test_publish_workflow_uses_trusted_publishing_with_release_guards():
    workflow = Path(".github/workflows/publish.yml").read_text(encoding="utf-8")

    assert "id-token: write" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "git fetch --no-tags origin main:refs/remotes/origin/main" in workflow
    assert "git fetch origin main --tags" not in workflow
    assert "Resolve package version" in workflow
    assert "Check tag matches package version" in workflow
    assert "Check release commit is on default branch" in workflow
    assert "Check PyPI version" in workflow
    assert "Fail when version is already on PyPI" in workflow
    assert "secrets.PYPI" not in workflow
    assert "TWINE_PASSWORD" not in workflow
    assert "PYPI_API_TOKEN" not in workflow
