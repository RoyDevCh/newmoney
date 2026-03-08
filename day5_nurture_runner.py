#!/usr/bin/env python3
"""Day-5 nurturing runner (Opinionated Expert phase)."""

from __future__ import annotations

import asyncio
import json
import random
import time
from datetime import datetime
from pathlib import Path

from adspower_runtime import AdsPowerClient, detect_base_url

API_KEY = "f4c41482d4a82fc23d53bf279279680300844ba1ed2698a4"
OUT_DIR = Path.home() / ".openclaw" / "workspace" / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = [
    {"name": "zhihu", "user_id": "k19yfy39", "url": "https://www.zhihu.com/", "keyword": "显卡 装机"},
    {"name": "xiaohongshu", "user_id": "k19yg15g", "url": "https://www.xiaohongshu.com/", "keyword": "显卡 装机"},
]

COMMENT_POOL = [
    "这个结论有参考价值，尤其是功耗和散热那段，建议再补一下测试环境参数。",
    "补充一点：同价位比较时建议把驱动成熟度和稳定帧也列进去，会更完整。",
    "信息密度很高，收藏了。实测场景如果再加1组对照数据就更有说服力。",
]


async def _type_slow(page, text: str):
    for ch in text:
        await page.keyboard.type(ch, delay=random.randint(60, 140))
        await asyncio.sleep(random.uniform(0.02, 0.08))


async def run_one(client: AdsPowerClient, target: dict):
    from playwright.async_api import async_playwright

    name = target["name"]
    uid = target["user_id"]
    url = target["url"]
    keyword = target["keyword"]

    screenshot = OUT_DIR / f"day5_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    result = {
        "platform": name,
        "ok": False,
        "comment_attempted": False,
        "comment_posted": False,
        "screenshot": str(screenshot),
        "error": "",
    }

    client.stop(uid)
    ws = client.get_ws(uid, allow_start=True)
    browser = None
    page = None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(ws)
            ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await ctx.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)

            # Search (day-5 vertical focus)
            try:
                box = await page.wait_for_selector('input[type="search"], input[placeholder*="搜索"], #search-input, #search-keyword', timeout=5000)
                await box.click()
                await _type_slow(page, keyword)
                await page.keyboard.press("Enter")
                await asyncio.sleep(4)
            except Exception:
                pass

            # Fragmented browsing 90-140s (compressed for test runtime)
            stay = random.randint(90, 140)
            start = time.time()
            while time.time() - start < stay:
                await page.mouse.wheel(0, random.randint(300, 900))
                await asyncio.sleep(random.uniform(1.5, 3.5))

            # Try one expert-style comment
            result["comment_attempted"] = True
            comment = random.choice(COMMENT_POOL)
            try:
                # enter content page first if clickable item exists
                cards = await page.query_selector_all("a, .note-item, .ContentItem, .video-item")
                if cards:
                    await cards[0].click()
                    await asyncio.sleep(3)

                cbox = await page.wait_for_selector('textarea, [contenteditable="true"], div[role="textbox"]', timeout=6000)
                await cbox.click()
                await _type_slow(page, comment)
                await asyncio.sleep(1)
                submit = await page.query_selector('button:has-text("发送"), button:has-text("发布"), button:has-text("评论"), button[type="submit"]')
                if submit:
                    await submit.click()
                    result["comment_posted"] = True
            except Exception:
                pass

            await page.screenshot(path=str(screenshot), full_page=True)
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
    for i, t in enumerate(order):
        if i > 0:
            time.sleep(random.randint(20, 60))
        results.append(await run_one(client, t))

    out = OUT_DIR / f"day5_nurture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(out), "ok": [r['platform'] for r in results if r['ok']]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
