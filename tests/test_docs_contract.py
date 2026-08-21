from pathlib import Path

from chatstyle import render_click_tree

from chatgame.cli import main


PUBLIC_DOCS_URL = "https://arch.gh.wzhecnu.cn/ChatGame/"


def _text_blocks(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [chunk.split("```", 1)[0].rstrip() for chunk in text.split("```text\n")[1:]]


def test_runtime_and_docs_dependency_contract():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert '"click>=8.0,<9.0"' in pyproject
    assert '"chatstyle>=0.2.0,<0.3.0"' in pyproject
    assert '"chatenv' not in pyproject
    assert '"mkdocs-material>=9.5,<9.7"' in pyproject


def test_docs_use_chatarch_public_domain_i18n_and_material_icon_renderer():
    config = Path("mkdocs.yml").read_text(encoding="utf-8")
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert f"site_url: {PUBLIC_DOCS_URL}" in config
    assert "name: material" in config
    assert "mkdocs-static-i18n" in pyproject
    assert "pymdownx.emoji" in config
    assert "material.extensions.emoji.twemoji" in config
    assert "material.extensions.emoji.to_svg" in config
    assert "cli-tree.md" in config
    assert "ChatGame/en/" in config
    assert f'Documentation = "{PUBLIC_DOCS_URL}"' in pyproject


def test_public_docs_do_not_reference_template_hello_command():
    checked = [
        Path("README.md"),
        Path("README.en.md"),
        Path("docs/index.md"),
        Path("docs/index.en.md"),
        Path("docs/cli.md"),
    ]
    for path in checked:
        text = path.read_text(encoding="utf-8").lower()
        assert "chatgame hello" not in text, path


def test_public_cli_docs_expose_full_and_brief_tree_commands():
    checked = [
        Path("README.md"),
        Path("README.en.md"),
        Path("docs/index.md"),
        Path("docs/index.en.md"),
        Path("docs/cli.md"),
    ]
    for path in checked:
        text = path.read_text(encoding="utf-8")
        assert "chatgame --tree" in text, path
        assert "chatgame --tree-brief" in text, path


def test_bilingual_cli_tree_docs_match_registered_full_and_brief_trees():
    expected = [
        render_click_tree(main, root_name="chatgame"),
        render_click_tree(main, root_name="chatgame", brief=True),
    ]

    for path in (Path("docs/cli-tree.md"), Path("docs/cli-tree.en.md")):
        text = path.read_text(encoding="utf-8")
        assert "chatstyle.add_tree_option()" in text
        assert "chatgame --tree" in text
        assert "chatgame --tree-brief" in text
        assert _text_blocks(path)[:2] == expected
