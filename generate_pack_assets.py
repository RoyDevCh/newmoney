#!/usr/bin/env python3
"""Generate platform cover assets from a monetization pack via ComfyUI."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests


SDXL_CHECKPOINT = "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"
FLUX_UNET = "flux1-schnell.safetensors"
FLUX_CLIP_L = "clip_l.safetensors"
FLUX_T5 = "text_encoder_2"
FLUX_VAE = "ae.safetensors"
COMFY_URL = "http://127.0.0.1:8188"
REMOTE_OUTPUT = Path.home() / "ComfyUI" / "output"
COMFY_MODELS = Path.home() / "ComfyUI" / "models"
WORKSPACE = Path.home() / ".openclaw" / "workspace"

SIZE_BY_PLATFORM = {
    "知乎": (1344, 768),
    "小红书": (832, 1216),
    "抖音": (864, 1536),
    "B站": (1536, 864),
    "微博": (1440, 1080),
    "公众号": (900, 383),
    "头条": (1200, 800),
    "西瓜视频": (1536, 864),
}

QUALITY_PRESETS = {
    "low": {"steps": 24, "cfg": 5.2, "suffix": "low"},
    "balanced": {"steps": 32, "cfg": 5.8, "suffix": "std"},
    "high": {"steps": 40, "cfg": 6.2, "suffix": "hq"},
}

FLUX_PRESETS = {
    "low": {"steps": 4, "guidance": 3.2, "suffix": "fluxlow"},
    "balanced": {"steps": 6, "guidance": 3.5, "suffix": "flux"},
    "high": {"steps": 8, "guidance": 4.0, "suffix": "fluxhq"},
}

DEFAULT_NEGATIVE = (
    "text, watermark, logo, lowres, blurry, extra fingers, deformed hands, "
    "duplicate subject, broken perspective, cluttered background"
)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to monetization pack JSON.")
    ap.add_argument("--platforms", nargs="*", default=[], help="Optional platform filter.")
    ap.add_argument("--max-images", type=int, default=8)
    ap.add_argument("--boot-comfy", action="store_true")
    ap.add_argument("--low-memory", action="store_true")
    ap.add_argument("--steps", type=int, default=0)
    ap.add_argument("--cfg", type=float, default=0.0)
    ap.add_argument("--quality-preset", choices=sorted(QUALITY_PRESETS.keys()), default="balanced")
    ap.add_argument("--manifest-out", default="")
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
        wanted = set(platforms)
        assets = [x for x in assets if str(x.get("platform", "")).strip() in wanted]
    return assets[:max_images]


def resolve_quality(args: argparse.Namespace, engine: str) -> Dict[str, Any]:
    if engine == "flux_schnell":
        preset = FLUX_PRESETS[args.quality_preset]
        steps = args.steps if args.steps > 0 else int(preset["steps"])
        guidance = float(preset["guidance"])
        return {"steps": steps, "cfg": 1.0, "guidance": guidance, "suffix": str(preset["suffix"])}
    preset = QUALITY_PRESETS[args.quality_preset]
    steps = args.steps if args.steps > 0 else int(preset["steps"])
    cfg = args.cfg if args.cfg > 0 else float(preset["cfg"])
    return {"steps": steps, "cfg": cfg, "guidance": 0.0, "suffix": str(preset["suffix"])}


def detect_model_inventory() -> Dict[str, Any]:
    flux_ready = all(
        [
            (COMFY_MODELS / "diffusion_models" / FLUX_UNET).exists(),
            (COMFY_MODELS / "text_encoders" / FLUX_CLIP_L).exists(),
            (COMFY_MODELS / "text_encoders" / FLUX_T5).exists(),
            (COMFY_MODELS / "vae" / FLUX_VAE).exists(),
        ]
    )
    checkpoint_ready = (COMFY_MODELS / "checkpoints" / SDXL_CHECKPOINT).exists()
    return {
        "flux_schnell": flux_ready,
        "sdxl_checkpoint": checkpoint_ready,
    }


def enrich_prompt_with_template(asset: Dict[str, Any], visual_templates: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    platform = str(asset.get("platform", "")).strip()
    prompt = str(asset.get("prompt", "")).strip()
    negative_prompt = str(asset.get("negative_prompt", "")).strip() or DEFAULT_NEGATIVE
    template = dict(visual_templates.get(platform, {}))
    if template:
        prompt = ", ".join(
            [
                prompt,
                str(template.get("subject_direction", "")).strip(),
                str(template.get("composition", "")).strip(),
                str(template.get("color_direction", "")).strip(),
                str(template.get("topic_palette", "")).strip(),
                str(template.get("typography_direction", "")).strip(),
            ]
        )
        negative_prompt = ", ".join(
            [
                negative_prompt,
                str(template.get("negative_prompt", "")).strip(),
                str(template.get("topic_negative_prompt", "")).strip(),
                "busy text blocks",
                "cheap poster layout",
                "misaligned title area",
                "theme mismatch",
            ]
        )
    return prompt, negative_prompt, template


def build_sdxl_workflow(
    asset: Dict[str, Any],
    visual_templates: Dict[str, Any],
    steps: int,
    cfg: float,
    suffix: str,
) -> Tuple[Dict[str, Any], str]:
    platform = str(asset.get("platform", "")).strip()
    width, height = SIZE_BY_PLATFORM.get(platform, (1024, 1024))
    seed = int(time.time() * 1000) % 2147483647
    prefix = f"oc_{platform}_{suffix}_{uuid.uuid4().hex[:8]}"
    prompt, negative_prompt, _ = enrich_prompt_with_template(asset, visual_templates)
    workflow = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": SDXL_CHECKPOINT}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": negative_prompt, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
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
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["6", 0]}},
    }
    return workflow, prefix


def build_flux_workflow(
    asset: Dict[str, Any],
    visual_templates: Dict[str, Any],
    steps: int,
    guidance: float,
    suffix: str,
) -> Tuple[Dict[str, Any], str]:
    platform = str(asset.get("platform", "")).strip()
    width, height = SIZE_BY_PLATFORM.get(platform, (1024, 1024))
    seed = int(time.time() * 1000) % 2147483647
    prefix = f"oc_{platform}_{suffix}_{uuid.uuid4().hex[:8]}"
    prompt, negative_prompt, _ = enrich_prompt_with_template(asset, visual_templates)
    workflow = {
        "1": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": FLUX_CLIP_L,
                "clip_name2": FLUX_T5,
                "type": "flux",
                "device": "default",
            },
        },
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 0]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": negative_prompt, "clip": ["1", 0]}},
        "4": {"class_type": "UNETLoader", "inputs": {"unet_name": FLUX_UNET, "weight_dtype": "default"}},
        "5": {"class_type": "VAELoader", "inputs": {"vae_name": FLUX_VAE}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "7": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["2", 0], "guidance": guidance}},
        "8": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["7", 0],
                "negative": ["3", 0],
                "latent_image": ["6", 0],
            },
        },
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["5", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["9", 0]}},
    }
    return workflow, prefix


def submit_prompt(workflow: Dict[str, Any]) -> str:
    r = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow}, timeout=20)
    r.raise_for_status()
    payload = r.json()
    if "error" in payload:
        raise RuntimeError(str(payload["error"]))
    return payload["prompt_id"]


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


def render_one_asset(
    asset: Dict[str, Any],
    visual_templates: Dict[str, Any],
    args: argparse.Namespace,
    inventory: Dict[str, Any],
) -> Dict[str, Any]:
    template = visual_templates.get(str(asset.get("platform", "")).strip(), {})
    image_strategy = str(template.get("image_strategy", "comfy_generated_ok")).strip() or "comfy_generated_ok"
    reference_queries = template.get("reference_search_queries", [])
    material_workflow = str(template.get("material_workflow", "")).strip()
    cover_layout_brief = str(template.get("cover_layout_brief", "")).strip()
    source_priority = template.get("source_priority", [])
    manual_asset_checklist = template.get("manual_asset_checklist", [])
    material_slots = template.get("material_slots", [])
    if image_strategy == "real_reference_preferred":
        return {
            "platform": asset.get("platform", ""),
            "exists": False,
            "engine": "real_reference_preferred",
            "skipped": True,
            "skip_reason": str(template.get("image_strategy_reason", "")).strip() or "real images convert better for this topic",
            "cover_strategy": image_strategy,
            "reference_search_queries": reference_queries,
            "material_workflow": material_workflow,
            "cover_layout_brief": cover_layout_brief,
            "source_priority": source_priority,
            "manual_asset_checklist": manual_asset_checklist,
            "material_slots": material_slots,
            "prompt_preview": str(asset.get("prompt", "")).strip(),
        }

    preferred_engine = str(template.get("model_hint", "flux_schnell")).strip()
    engine_order = [preferred_engine, "sdxl_checkpoint"] if preferred_engine != "sdxl_checkpoint" else ["sdxl_checkpoint"]
    if "flux_schnell" not in engine_order:
        engine_order.insert(0, "flux_schnell")

    errors: List[Dict[str, str]] = []
    for engine in engine_order:
        if not inventory.get(engine):
            errors.append({"engine": engine, "error": "model_not_available"})
            continue
        settings = resolve_quality(args, engine)
        try:
            if engine == "flux_schnell":
                workflow, prefix = build_flux_workflow(
                    asset,
                    visual_templates=visual_templates,
                    steps=int(settings["steps"]),
                    guidance=float(settings["guidance"]),
                    suffix=str(settings["suffix"]),
                )
            else:
                workflow, prefix = build_sdxl_workflow(
                    asset,
                    visual_templates=visual_templates,
                    steps=int(settings["steps"]),
                    cfg=float(settings["cfg"]),
                    suffix=str(settings["suffix"]),
                )
            prompt_id = submit_prompt(workflow)
            history = wait_for_history(prompt_id, timeout=900)
            out_path = resolve_output(history)
            return {
                "platform": asset.get("platform", ""),
                "prompt_id": prompt_id,
                "prefix": prefix,
                "output_file": str(out_path),
                "exists": out_path.exists(),
                "size_mb": round(out_path.stat().st_size / (1024 * 1024), 2) if out_path.exists() else 0.0,
                "quality_preset": args.quality_preset,
                "steps": int(settings["steps"]),
                "cfg": float(settings["cfg"]),
                "guidance": float(settings["guidance"]),
                "engine": engine,
                "cover_strategy": image_strategy,
                "reference_search_queries": reference_queries,
                "material_workflow": material_workflow,
                "cover_layout_brief": cover_layout_brief,
                "source_priority": source_priority,
                "manual_asset_checklist": manual_asset_checklist,
                "material_slots": material_slots,
                "fallback_errors": errors,
            }
        except Exception as exc:
            errors.append({"engine": engine, "error": str(exc)})
            continue

    return {
        "platform": asset.get("platform", ""),
        "exists": False,
        "engine": "failed",
        "cover_strategy": image_strategy,
        "reference_search_queries": reference_queries,
        "material_workflow": material_workflow,
        "cover_layout_brief": cover_layout_brief,
        "source_priority": source_priority,
        "manual_asset_checklist": manual_asset_checklist,
        "material_slots": material_slots,
        "fallback_errors": errors,
    }


def main() -> None:
    args = parse_args()
    pack = load_pack(Path(args.input))
    assets = select_assets(pack, args.platforms, args.max_images)
    visual_templates = pack.get("visual_templates", {})
    if not assets:
        raise SystemExit("No eligible assets found.")

    needs_comfy = any(
        str(visual_templates.get(str(asset.get("platform", "")).strip(), {}).get("image_strategy", "comfy_generated_ok")).strip()
        != "real_reference_preferred"
        for asset in assets
    )
    if needs_comfy and not comfy_online():
        if not args.boot_comfy:
            raise SystemExit("ComfyUI offline. Re-run with --boot-comfy.")
        start_comfy(low_memory=args.low_memory)
        if not comfy_online():
            raise SystemExit("ComfyUI failed to start.")

    inventory = detect_model_inventory()
    results = [render_one_asset(asset, visual_templates, args, inventory) for asset in assets]

    payload = {
        "source_pack": args.input,
        "quality_preset": args.quality_preset,
        "model_inventory": inventory,
        "results": results,
    }
    if args.manifest_out:
        Path(args.manifest_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
