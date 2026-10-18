"""Small offline maintenance CLI. No implicit asset downloads."""

import argparse
import json

from . import available_constellations, clear_cache, verify_assets


def main():
    parser = argparse.ArgumentParser(prog="starplot-art")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List bundled IAU abbreviations")
    sub.add_parser("verify", help="Verify all bundled assets offline")
    clear = sub.add_parser("clear-cache", help="Clear only this package's rendered-image cache")
    clear.add_argument("--directory")
    args = parser.parse_args()
    if args.command == "list":
        print(" ".join(available_constellations()))
    elif args.command == "verify":
        print(json.dumps(verify_assets(), indent=2))
    else:
        print(f"Removed {clear_cache(args.directory)} cached records")
