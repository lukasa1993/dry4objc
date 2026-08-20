from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import find_duplicates


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Find duplicated token blocks in Objective-C source.")
    value.add_argument("filters", nargs="*")
    value.add_argument("--root", type=Path, default=Path("."))
    value.add_argument("--min-tokens", type=int, default=40)
    value.add_argument("--max-groups", type=int, default=50)
    value.add_argument("--json", action="store_true", dest="json_output")
    value.add_argument("--fail", action="store_true")
    value.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        duplicates = find_duplicates(args.root.resolve(), args.min_tokens, args.filters, args.max_groups)
    except (OSError, ValueError) as error:
        print(f"dry4objc: {error}", file=sys.stderr)
        return 1
    if args.json_output:
        print(json.dumps([item.to_dict() for item in duplicates], indent=2, sort_keys=True))
    elif not duplicates:
        print("No duplicated blocks found.")
    else:
        print("DRY Report\n==========")
        for index, duplicate in enumerate(duplicates, 1):
            print(f"\nGroup {index}: {duplicate.token_count} normalized tokens")
            for location in duplicate.locations:
                print(f"  {location.file}:{location.start_line}-{location.end_line}")
    return 2 if args.fail and duplicates else 0
