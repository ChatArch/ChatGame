from pathlib import Path


PUBLIC_DOCS_URL = "https://arch.gh.wzhecnu.cn/ChatGame/"


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
