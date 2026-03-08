#!/usr/bin/env python3
"""Smoke test all platform profiles via AdsPower CDP."""

from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime
from pathlib import Path

from adspower_runtime import AdsPowerClient, detect_base_url

API_KEY = "f4c41482d4a82fc23d53bf279279680300844ba1ed2698a4"
ROOT = Path.home() / ".openclaw"
OUT_DIR = ROOT / "workspace" / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = [
    {"name": "weibo", "user_id": "k19yg5a3", "url": "https://weibo.com/"},
    {"name": "xiaohongshu", "user_id": "k19yg15g", "url": "https://www.xiaohongshu.com/"},
    {"name": "gzh", "user_id": "k19yg2eg", "url": "https://mp.weixin.qq.com/"},
    {"name": "zhihu", "user_id": "k19yfy39", "url": "https://www.zhihu.com/"},
    {"name": "douyin", "user_id": "k19yftx6", "url": "https://www.douyin.com/"},
    {"name": "bilibili", "user_id": "k19yg4ce", "url": "https://www.bilibili.com/"},
    {"name": "toutiao", "user_id": "k19yg3dv", "url": "https://www.toutiao.com/"},
]


async def test_one(client: AdsPowerClient, target: dict):
    from playwright.async_api import async_playwright

    name = target["name"]
    uid = target["user_id"]
    url = target["url"]
    img = OUT_DIR / f"smoke_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    client.stop(uid)
    ws = client.get_ws(uid, allow_start=True)

    browser = None
    page = None
    result = {"platform": name, "ok": False, "title": "", "screenshot": str(img), "error": ""}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(ws)
            ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await ctx.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2.0, 4.0))
            await page.mouse.wheel(0, random.randint(300, 800))
            await asyncio.sleep(random.uniform(1.0, 2.0))
            result["title"] = await page.title()
            await page.screenshot(path=str(img), full_page=True)
            result["ok"] = True
    except Exception as e:
        result["error"] = str(e)
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
        client.stop(uid)

    return result


async def main():
    client = AdsPowerClient(api_key=API_KEY, base_url=detect_base_url())
    order = TARGETS[:]
    random.shuffle(order)
    results = []
    for t in order:
        results.append(await test_one(client, t))

    out = OUT_DIR / f"platform_smoke_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(out), "ok": [x['platform'] for x in results if x['ok']]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
