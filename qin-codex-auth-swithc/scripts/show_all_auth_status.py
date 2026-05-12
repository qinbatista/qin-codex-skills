#!/usr/bin/env python3

import argparse
import importlib.util
import sys
from pathlib import Path


def load_manager():
    script_dir = Path(__file__).resolve().parent
    manager_path = script_dir / "manage_auth_profiles.py"
    spec = importlib.util.spec_from_file_location("manage_auth_profiles", manager_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_parser():
    parser = argparse.ArgumentParser(
        description="Show live Codex auth status for saved auth files, optionally switching first."
    )
    parser.add_argument(
        "selector",
        nargs="?",
        help="Optional auth selector to switch to before showing status, for example auth_qin.json",
    )
    return parser


def main():
    args = build_parser().parse_args()
    module = load_manager()
    codex_home = Path.home() / ".codex"
    if args.selector:
        profiles = module.discover_profiles(codex_home=codex_home, threads_limit=800, live=False)
        profile = module.resolve_profile(profiles, args.selector)
        source = Path(profile["path"])
        destination = codex_home / "auth.json"
        if source.resolve() != destination.resolve():
            module.shutil.copyfile(source, destination)
    profiles = module.discover_profiles(
        codex_home=codex_home,
        threads_limit=800,
        live=True,
        workdir=Path.cwd(),
        live_prompt=module.DEFAULT_LIVE_PROMPT,
    )
    module.print_profiles(profiles)


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
