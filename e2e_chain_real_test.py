#!/usr/bin/env python3
"""Real end-to-end chain test for OpenClaw on Windows host."""

from __future__ import annotations

import asyncio
import ctypes
import json
import os
import random
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests

from adspower_runtime import AdsPowerClient, detect_base_url
from news_guard import NewsCheckResult, check_topic


API_KEY = os.getenv("ADSPOWER_API_KEY", "f4c41482d4a82fc23d53bf279279680300844ba1ed2698a4")
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://127.0.0.1:8080")
VOCECHAT_BASE = os.getenv("VOCECHAT_BASE", "http://127.0.0.1:3009")
BRIDGE_WEBHOOK = os.getenv("BRIDGE_WEBHOOK", "http://127.0.0.1:8091/")
WORKSPACE = Path.home() / ".openclaw" / "workspace"
REPORT_DIR = WORKSPACE / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
OPENCLAW_BIN = Path(os.getenv("OPENCLAW_BIN", str(Path.home() / "AppData" / "Roaming" / "npm" / "openclaw.cmd")))

PROFILE_IDS = {
    "zhihu": "k19yfy39",
    "xiaohongshu": "k19yg15g",
    "bilibili": "k19yg4ce",
}

VOCECHAT_KEYS = {
    "main": os.getenv(
        "VOCECHAT_MAIN_KEY",
        "39d6430f7f9a03d6ece8aa70d5540672debfe28c155d9774c89c881d8c05c2517b22756964223a382c226e6f6e6365223a22705066444938384872476b414141414156317a43616b7376686637446c66787a227d",
    ),
    "tasks": os.getenv(
        "VOCECHAT_TASKS_KEY",
        "745003e8e0bd479231da7be4b00e63b973e108dca24c9d01c1d602e3834100907b22756964223a372c226e6f6e6365223a226c445a714772774872476b4141414141626445417972564e67626a4a616f7264227d",
    ),
}


@dataclass
class PlatformResult:
    platform: str
    ok: bool
    has_captcha: bool
    title: str
    screenshot: str
    duration_sec: float
    error: str = ""


@dataclass
class ComfyResult:
    ok: bool
    model: str
    duration_sec: float
    image_file: str
    image_size_mb: float
    quality_proxy: float
    error: str = ""


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def memory_snapshot() -> Dict[str, float]:
    m = MEMORYSTATUSEX()
    m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    gb = 1024**3
    return {
        "total_gb": round(m.ullTotalPhys / gb, 2),
        "free_gb": round(m.ullAvailPhys / gb, 2),
        "used_percent": round(float(m.dwMemoryLoad), 2),
    }


def run_openclaw_agent(agent: str, message: str, timeout: int = 240) -> Dict:
    cmd = ["cmd", "/c", str(OPENCLAW_BIN), "agent", "--agent", agent, "--message", message, "--timeout", str(timeout)]
    start = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout + 30)
        return {
            "ok": p.returncode == 0,
            "duration_sec": round(time.time() - start, 2),
            "stdout": (p.stdout or "").strip()[:1600],
            "stderr": (p.stderr or "").strip()[:1200],
            "returncode": p.returncode,
        }
    except Exception as exc:
        return {
            "ok": False,
            "duration_sec": round(time.time() - start, 2),
            "stdout": "",
            "stderr": str(exc),
            "returncode": -1,
        }


def test_agent_collaboration() -> Dict:
    main_out = run_openclaw_agent(
        "main",
        "请生成一个给 tasks 的一句话执行任务，主题是'验证知乎首页可访问并截图'，只输出任务文本本身。",
    )

    task_message = main_out.get("stdout") or "验证知乎首页可访问并截图，然后简短汇报结果。"
    tasks_out = run_openclaw_agent("tasks", task_message)

    webhook_payload = {
        "mid": f"e2e-{uuid.uuid4()}",
        "target": {"gid": 1},
        "from_uid": 8,
        "detail": {
            "type": "normal",
            "content": "@tasks E2E 协作测试：请回复 TASKS_OK",
            "properties": {"mentions": [{"uid": 7}]},
        },
    }

    bridge_status = {"ok": False, "status": 0, "body": ""}
    try:
        r = requests.post(BRIDGE_WEBHOOK, json=webhook_payload, timeout=10)
        bridge_status = {"ok": r.status_code == 200, "status": r.status_code, "body": r.text[:200]}
    except Exception as exc:
        bridge_status = {"ok": False, "status": 0, "body": str(exc)}

    vocechat_status = {}
    for who, key in VOCECHAT_KEYS.items():
        try:
            resp = requests.post(
                f"{VOCECHAT_BASE}/api/bot/send_to_group/1",
                data=f"[E2E] hello from {who}".encode("utf-8"),
                headers={"x-api-key": key, "content-type": "text/plain"},
                timeout=8,
            )
            vocechat_status[who] = {"ok": resp.status_code == 200, "status": resp.status_code}
        except Exception as exc:
            vocechat_status[who] = {"ok": False, "status": 0, "error": str(exc)}

    return {
        "openclaw_bin": str(OPENCLAW_BIN),
        "main_to_tasks_handoff": main_out,
        "tasks_execution": tasks_out,
        "bridge_webhook": bridge_status,
        "vocechat_send": vocechat_status,
    }


async def check_captcha(page) -> bool:
    selectors = [
        "#captcha-verify-container",
        ".secsdk-captcha-drag-icon",
        ".geetest_captcha",
        "#nc_wrapper",
        'iframe[src*="verify.snssdk.com"]',
        'iframe[src*="captcha"]:not([src*="qrcode"])',
    ]
    precise = ", ".join(selectors)
    try:
        await page.wait_for_selector(precise, state="visible", timeout=3000)
        return True
    except Exception:
        return False


async def _attempt_platform(client: AdsPowerClient, platform: str, url: str, out_png: Path) -> PlatformResult:
    from playwright.async_api import async_playwright

    user_id = PROFILE_IDS[platform]
    start = time.time()
    ws = client.get_ws(user_id=user_id, allow_start=True)

    browser = None
    page = None
    title = ""
    has_captcha = False

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(ws)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2.0, 4.0))
            has_captcha = await check_captcha(page)
            title = await page.title()
            await page.screenshot(path=str(out_png), full_page=True)

        return PlatformResult(
            platform=platform,
            ok=not has_captcha,
            has_captcha=has_captcha,
            title=title,
            screenshot=str(out_png),
            duration_sec=round(time.time() - start, 2),
        )
    except Exception as exc:
        return PlatformResult(
            platform=platform,
            ok=False,
            has_captcha=has_captcha,
            title=title,
            screenshot=str(out_png),
            duration_sec=round(time.time() - start, 2),
            error=str(exc),
        )
    finally:
        try:
            if page:
                await page.close()
        except Exception:
            pass
        try:
            if browser:
                await browser.disconnect()
        except Exception:
            pass
        client.stop(user_id)


async def run_platform_smoke(client: AdsPowerClient, platform: str, url: str) -> PlatformResult:
    user_id = PROFILE_IDS[platform]
    out_png = REPORT_DIR / f"{platform}_{int(time.time())}.png"

    # Force recycle once before each platform to reduce stale CDP sessions.
    client.stop(user_id)
    time.sleep(1)

    first = await _attempt_platform(client, platform, url, out_png)
    if first.ok:
        return first

    retryable = "ERR_CONNECTION_CLOSED" in first.error or "Target page, context or browser has been closed" in first.error
    if not retryable:
        return first

    time.sleep(2)
    client.stop(user_id)
    time.sleep(2)
    second = await _attempt_platform(client, platform, url, out_png)
    if second.ok:
        return second

    second.error = f"retry_failed | first_error={first.error} | second_error={second.error}"
    return second


def list_checkpoints() -> List[str]:
    ckpt_dir = Path.home() / "ComfyUI" / "models" / "checkpoints"
    if not ckpt_dir.exists():
        return []
    return sorted([p.name for p in ckpt_dir.iterdir() if p.is_file() and p.suffix in {".safetensors", ".ckpt"}])


def comfy_online(base_url: str = "http://127.0.0.1:8188") -> bool:
    try:
        r = requests.get(f"{base_url}/object_info", timeout=4)
        return r.status_code == 200
    except Exception:
        return False


def start_comfyui_if_needed() -> Optional[subprocess.Popen]:
    if comfy_online():
        return None

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    log_path = REPORT_DIR / "comfyui_boot.log"
    logf = open(log_path, "a", encoding="utf-8")

    main_py = Path.home() / "ComfyUI" / "main.py"
    p = subprocess.Popen(
        [sys.executable, str(main_py), "--listen", "127.0.0.1", "--port", "8188", "--directml"],
        cwd=str(Path.home() / "ComfyUI"),
        stdout=logf,
        stderr=logf,
        creationflags=creationflags,
    )

    for _ in range(120):
        if comfy_online():
            return p
        time.sleep(2)
    return p


def benchmark_comfy_model(model_name: str) -> ComfyResult:
    prompt = (
        "ultra detailed cyberpunk city at dusk, volumetric lighting, cinematic composition, "
        "high contrast, clean textures, professional color grading"
    )

    workflow = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model_name}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "lowres, blurry, watermark, deformed, text",
                "clip": ["1", 1],
            },
        },
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": int(time.time()),
                "steps": 24,
                "cfg": 7.5,
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
        "7": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "e2e_quality_test", "images": ["6", 0]},
        },
    }

    start = time.time()
    try:
        resp = requests.post("http://127.0.0.1:8188/prompt", json={"prompt": workflow}, timeout=15)
        resp.raise_for_status()
        prompt_id = resp.json().get("prompt_id")
        if not prompt_id:
            raise RuntimeError("No prompt_id returned")

        task = None
        for _ in range(180):
            h = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}", timeout=8)
            if h.status_code == 200:
                data = h.json()
                task = data.get(prompt_id)
                if task and task.get("status", {}).get("completed"):
                    break
            time.sleep(2)

        if not task or not task.get("status", {}).get("completed"):
            raise RuntimeError("ComfyUI generation timeout")

        image_file = ""
        file_size_mb = 0.0
        outputs = task.get("outputs", {})
        for _, node_data in outputs.items():
            images = node_data.get("images")
            if not images:
                continue
            img = images[0]
            sub = img.get("subfolder", "")
            name = img.get("filename", "")
            p = Path.home() / "ComfyUI" / "output"
            full = p / sub / name if sub else p / name
            image_file = str(full)
            if full.exists():
                file_size_mb = round(full.stat().st_size / (1024 * 1024), 3)
            break

        duration = round(time.time() - start, 2)
        quality_proxy = round(min(file_size_mb / 4.0, 1.0) * 0.7 + min(20.0 / max(duration, 1.0), 1.0) * 0.3, 4)
        return ComfyResult(
            ok=True,
            model=model_name,
            duration_sec=duration,
            image_file=image_file,
            image_size_mb=file_size_mb,
            quality_proxy=quality_proxy,
        )
    except Exception as exc:
        return ComfyResult(
            ok=False,
            model=model_name,
            duration_sec=round(time.time() - start, 2),
            image_file="",
            image_size_mb=0.0,
            quality_proxy=0.0,
            error=str(exc),
        )


def test_video_pipeline() -> Dict:
    mem_before = memory_snapshot()
    if mem_before["free_gb"] < 5.0:
        return {
            "ok": False,
            "reason": "low_memory_before_video_stage",
            "memory_before": mem_before,
        }

    proc = start_comfyui_if_needed()
    if not comfy_online():
        return {
            "ok": False,
            "reason": "comfyui_not_reachable",
            "memory_before": mem_before,
        }

    models = list_checkpoints()
    if not models:
        return {
            "ok": False,
            "reason": "no_checkpoints_found",
            "memory_before": mem_before,
        }

    results = [asdict(benchmark_comfy_model(m)) for m in models]
    best = max(results, key=lambda x: x.get("quality_proxy", 0.0))

    if proc is not None:
        try:
            proc.terminate()
        except Exception:
            pass

    return {
        "ok": True,
        "memory_before": mem_before,
        "memory_after": memory_snapshot(),
        "models_tested": models,
        "best_model": best,
        "results": results,
    }


def run_news_guard() -> Dict:
    queries = [
        "OpenAI 最新 模型 发布",
        "NVIDIA AMD AI 显卡 最新 动态",
    ]
    outputs: List[NewsCheckResult] = []
    for q in queries:
        try:
            items = check_topic(SEARXNG_URL, q)
            outputs.append(items)
        except Exception as exc:
            outputs.append(
                NewsCheckResult(
                    query=q,
                    confidence=0.0,
                    is_publishable=False,
                    reasons=[f"fetch_error:{exc}"],
                    trusted_hits=0,
                    recent_hits=0,
                    sampled_titles=[],
                )
            )

    return {
        "searxng_url": SEARXNG_URL,
        "checks": [asdict(x) for x in outputs],
        "policy": {
            "publish_only_if": "confidence>=0.65 and trusted_hits>=2 and recent_hits>=1",
            "action_on_fail": "hold_and_manual_review",
        },
    }


async def main() -> None:
    report: Dict = {
        "timestamp": utc_now(),
        "host": os.environ.get("COMPUTERNAME", "unknown"),
        "memory_at_start": memory_snapshot(),
        "adspower_base_url": "",
        "agent_collaboration": {},
        "platform_tests": [],
        "video_pipeline": {},
        "news_guard": {},
        "resource_strategy": {
            "mode": "tide",
            "rules": [
                "strict_serial_execution",
                "close_cdp_and_stop_profile_after_each_platform",
                "skip_video_stage_if_free_ram_lt_5gb",
                "terminate_comfyui_if_started_by_test",
            ],
        },
    }

    try:
        report["adspower_base_url"] = detect_base_url()
    except Exception as exc:
        report["fatal"] = f"adspower_unavailable: {exc}"

    report["agent_collaboration"] = test_agent_collaboration()

    if report.get("adspower_base_url"):
        client = AdsPowerClient(api_key=API_KEY, base_url=report["adspower_base_url"])
        tests = [
            ("zhihu", "https://www.zhihu.com/"),
            ("xiaohongshu", "https://www.xiaohongshu.com/"),
        ]
        for name, url in tests:
            r = await run_platform_smoke(client, name, url)
            report["platform_tests"].append(asdict(r))
            time.sleep(random.randint(8, 18))

    report["video_pipeline"] = test_video_pipeline()
    report["news_guard"] = run_news_guard()
    report["memory_at_end"] = memory_snapshot()

    out = REPORT_DIR / f"e2e_chain_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(out),
                "summary": {
                    "adspower": report.get("adspower_base_url", ""),
                    "platform_ok": [x.get("platform") for x in report.get("platform_tests", []) if x.get("ok")],
                    "video_ok": report.get("video_pipeline", {}).get("ok"),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())

