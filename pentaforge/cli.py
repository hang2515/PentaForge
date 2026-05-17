#!/usr/bin/env python3
"""PentaForge CLI — semi-automatic League of Legends highlight clipping tool."""

import argparse
import sys
import os

from src.config_parser import load_config
from src.pipeline import run_pipeline, cleanup_temp


def main():
    parser = argparse.ArgumentParser(
        description="PentaForge — LoL Highlight Clipper"
    )
    parser.add_argument(
        "config",
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary files after processing (for debugging)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="PentaForge 0.1.0",
    )
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Error: config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading config: {args.config}")
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error parsing config: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Source: {config.source}")
    print(f"Clips: {len(config.clips)}")
    for i, clip in enumerate(config.clips):
        print(f"  [{i}] {clip.start:.1f}s - {clip.end:.1f}s ({clip.duration:.1f}s)"
              f"{' ' + clip.kill_type if clip.kill_type else ''}"
              f"{' ' + clip.label if clip.label else ''}")

    print("Processing...")
    result = run_pipeline(config)

    if result.success:
        print(f"Done: {result.output_path}")
    else:
        print(f"Failed: {result.errors}", file=sys.stderr)
        sys.exit(1)

    if not args.keep_temp and result.temp_dir:
        cleanup_temp(result.temp_dir)


if __name__ == "__main__":
    main()
