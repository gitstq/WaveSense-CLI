"""
WaveSense-CLI - 模块入口点 / Module Entry Point
==================================================

允许通过 python -m wavesense_cli 运行。
Allows running via python -m wavesense_cli.

用法 / Usage:
    python -m wavesense_cli scan
    python -m wavesense_cli dashboard
    python -m wavesense_cli --help
"""

import sys


def main() -> None:
    """入口函数 / Entry function"""
    from .cli import main as cli_main
    sys.exit(cli_main())


if __name__ == "__main__":
    main()
