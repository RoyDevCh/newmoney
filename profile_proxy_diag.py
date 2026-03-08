#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
from adspower_runtime import AdsPowerClient, detect_base_url

API_KEY = "f4c41482d4a82fc23d53bf279279680300844ba1ed2698a4"
PROFILES = {
    "zhihu": "k19yfy39",
    "xiaohongshu": "k19yg15g",
}
URLS = [
    "https://www.zhihu.com/",
    "https://www.xiaohongshu.com/",
    "https://example.com/",
    "http://1.1.1.1/",
]


async def check_profile(name: str, uid: str):
    from playwright.async_api import async_playwright

    client = AdsPowerClient(API_KEY, detect_base_url())
    client.stop(uid)
    ws = client.get_ws(uid, allow_start=True)
    out = {"profile": name, "user_id": uid, "checks": []}

    browser = None
    page = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(ws)
            ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await ctx.new_page()
            for u in URLS:
                try:
                    await page.goto(u, wait_until="domcontentloaded", timeout=30000)
                    out["checks"].append({"url": u, "ok": True, "title": await page.title()})
                except Exception as e:
                    out["checks"].append({"url": u, "ok": False, "error": str(e)[:220]})
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
    return out


async def main():
    results = []
    for n, u in PROFILES.items():
        results.append(await check_profile(n, u))
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
