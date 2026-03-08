#!/usr/bin/env python3
"""Generate cover assets from a monetization pack via ComfyUI."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests


CHECKPOINT = "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"
COMFY_URL = "http://127.0.0.1:8188"
REMOTE_OUTPUT = Path.home() / "ComfyUI" / "output"
WORKSPACE = Path.home() / ".openclaw" / "workspace"

SIZE_BY_PLATFORM = {
    "知乎": (1344, 768),
    "小红书": (832, 1216),
    "抖音": (864, 1536),
    "B站": (1536, 864),
}


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to monetization pack JSON.")
    ap.add_argument("--platforms", nargs="*", default=[], help="Optional platform filter.")
    ap.add_argument("--max-images", type=int, default=4)
    ap.add_argument("--boot-comfy", action="store_true")
    ap.add_argument("--low-memory", action="store_true")
    ap.add_argument("--steps", type=int, default=32)
    ap.add_argument("--cfg", type=float, default=5.8)
    return ap.parse_args()


def comfy_online() -> bool:
    try:
        r = requests.get(f"{COMFY_URL}/object_info", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def start_comfy(low_memory: bool) -> None:
    launcher = WORKSPACE / "start_comfy_directml.py"
    cmd = ["py", "-3", str(launcher)]
    if low_memory:
        cmd.extend(["--extra-args", "--disable-auto-launch --cpu-vae"])
    else:
        cmd.extend(["--extra-args", "--disable-auto-launch"])
    subprocess.run(cmd, check=True, timeout=420)


def load_pack(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def select_assets(pack: Dict[str, Any], platforms: List[str], max_images: int) -> List[Dict[str, Any]]:
    assets = [x for x in pack.get("assets", []) if isinstance(x, dict) and x.get("prompt")]
    if platforms:
        want = set(platforms)
        assets = [x for x in assets if str(x.get("platform", "")).strip() in want]
    return assets[:max_images]


def build_workflow(asset: Dict[str, Any], steps: int, cfg: float) -> Tuple[Dict[str, Any], str]:
    platform = str(asset.get("platform", "")).strip()
    width, height = SIZE_BY_PLATFORM.get(platform, (1024, 1024))
    seed = int(time.time() * 1000) % 2147483647
    prefix = f"oc_{platform}_{uuid.uuid4().hex[:8]}"
    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": CHECKPOINT},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": str(asset.get("prompt", "")),
                "clip": ["1", 1],
            },
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": str(asset.get("negative_prompt", "")),
                "clip": ["1", 1],
            },
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1,
            },
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
            },
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["1", 2],
            },
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": prefix,
                "images": ["6", 0],
            },
        },
    }
    return workflow, prefix


def submit_prompt(workflow: Dict[str, Any]) -> str:
    r = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow}, timeout=20)
    r.raise_for_status()
    return r.json()["prompt_id"]


def wait_for_history(prompt_id: str, timeout: int = 600) -> Dict[str, Any]:
    started = time.time()
    while time.time() - started < timeout:
        r = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
        r.raise_for_status()
        data = r.json()
        if prompt_id in data and data[prompt_id].get("status", {}).get("completed", False):
            return data[prompt_id]
        time.sleep(3)
    raise TimeoutError(f"Timed out waiting for prompt {prompt_id}")


def resolve_output(task_data: Dict[str, Any]) -> Path:
    outputs = task_data.get("outputs", {})
    for node_data in outputs.values():
        images = node_data.get("images", [])
        if images:
            image = images[0]
            subfolder = image.get("subfolder", "")
            filename = image.get("filename", "")
            base = REMOTE_OUTPUT / subfolder if subfolder else REMOTE_OUTPUT
            return base / filename
    raise FileNotFoundError("No image output found in history")


def main() -> None:
    args = parse_args()
    if not comfy_online():
        if not args.boot_comfy:
            raise SystemExit("ComfyUI offline. Re-run with --boot-comfy.")
        start_comfy(low_memory=args.low_memory)
        if not comfy_online():
            raise SystemExit("ComfyUI failed to start.")

    pack = load_pack(Path(args.input))
    assets = select_assets(pack, args.platforms, args.max_images)
    if not assets:
        raise SystemExit("No eligible assets found.")

    results = []
    for asset in assets:
        workflow, prefix = build_workflow(asset, steps=args.steps, cfg=args.cfg)
        prompt_id = submit_prompt(workflow)
        history = wait_for_history(prompt_id)
        out_path = resolve_output(history)
        results.append(
            {
                "platform": asset.get("platform", ""),
                "prompt_id": prompt_id,
                "prefix": prefix,
                "output_file": str(out_path),
                "exists": out_path.exists(),
                "size_mb": round(out_path.stat().st_size / (1024 * 1024), 2) if out_path.exists() else 0.0,
            }
        )

    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
