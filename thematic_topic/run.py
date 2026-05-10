"""CLI実行用。"""

from __future__ import annotations

import argparse

from .pipeline import run_pipeline



def main() -> None:
    parser = argparse.ArgumentParser(description="thematic-topic pipeline")
    parser.add_argument("--config", default="config/default.yaml", help="設定YAMLパス")
    args = parser.parse_args()

    run_pipeline(args.config)


if __name__ == "__main__":
    main()
