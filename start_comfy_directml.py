#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import requests


def comfy_online() -> bool:
    try:
        r = requests.get("http://127.0.0.1:8188/object_info", timeout=4)
        return r.status_code == 200
    except Exception:
        return False


def build_command(args: argparse.Namespace, main_py: Path) -> list[str]:
    cmd = [sys.executable, str(main_py), "--listen", args.host, "--port", str(args.port), "--directml"]
    extra_args = [x for x in (args.extra_args or "").split(" ") if x.strip()]
    cmd.extend(extra_args)
    return cmd


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.getenv("COMFYUI_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.getenv("COMFYUI_PORT", "8188")))
    ap.add_argument("--timeout-sec", type=int, default=int(os.getenv("COMFYUI_BOOT_TIMEOUT_SEC", "300")))
    ap.add_argument("--extra-args", default=os.getenv("COMFYUI_EXTRA_ARGS", ""))
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    if comfy_online():
        print("ALREADY_ONLINE")
        return 0

    wd = Path.home() / "ComfyUI"
    main_py = wd / "main.py"
    if not main_py.exists():
        print(f"MISSING_MAIN:{main_py}")
        return 2

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    log_path = Path.home() / ".openclaw" / "workspace" / "reports" / "comfyui_directml_boot.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logf = open(log_path, "a", encoding="utf-8")

    cmd = build_command(args, main_py)
    print("BOOT_CMD:" + " ".join(cmd))

    subprocess.Popen(
        cmd,
        cwd=str(wd),
        stdout=logf,
        stderr=logf,
        creationflags=creationflags,
    )

    for _ in range(max(args.timeout_sec // 2, 1)):
        if comfy_online():
            print("ONLINE")
            return 0
        time.sleep(2)

    print("FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
