"""CLI entrypoint for chatgame — 待设计。"""

import click


@click.group()
def main() -> None:
    """chatgame — 游戏谜题求解工具。"""


if __name__ == "__main__":
    main()
