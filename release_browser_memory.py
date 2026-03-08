#!/usr/bin/env python3
"""Explicitly stop AdsPower browser profiles to free RAM after tests or publishing."""

from __future__ import annotations

import argparse
import json
import os
from typing import List

from adspower_runtime import AdsPowerClient, detect_base_url


DEFAULT_PROFILES = {
    "weibo": "k19yg5a3",
    "xiaohongshu": "k19yg15g",
    "gzh": "k19yg2eg",
    "zhihu": "k19yfy39",
    "douyin": "k19yftx6",
    "bilibili": "k19yg4ce",
    "toutiao": "k19yg3dv",
}


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-key", default=os.getenv("ADSPOWER_API_KEY", ""))
    ap.add_argument("--base-url", default=os.getenv("ADSPOWER_BASE_URL", ""))
    ap.add_argument("--all", action="store_true", help="Stop all known platform profiles.")
    ap.add_argument("--profiles", nargs="*", default=[], help="Profile ids or known platform aliases.")
    return ap.parse_args()


def resolve_profiles(values: List[str], stop_all: bool) -> List[str]:
    if stop_all:
        return list(DEFAULT_PROFILES.values())
    resolved = []
    for value in values:
        resolved.append(DEFAULT_PROFILES.get(value, value))
    return resolved


def main() -> None:
    args = parse_args()
    profile_ids = resolve_profiles(args.profiles, args.all)
    if not profile_ids:
        raise SystemExit("No profiles selected. Use --all or --profiles.")

    client = AdsPowerClient(
        api_key=args.api_key,
        base_url=args.base_url or detect_base_url(),
    )
    result = client.stop_many(profile_ids)
    print(json.dumps({"base_url": client.base_url, "stopped": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
