# -*- coding: utf-8 -*-
"""Playwright + 系统 Chrome 批量截取系统功能界面（软著补正用）。

用法：
  python shoot_pages.py --base http://localhost:82 --out SHOTS \
      --token-file SHOTS/token.txt --info-file SHOTS/info.json \
      --pages SHOTS/pages.json --login-path /content/column

pages.json: [["01_dashboard", "/dashboard", "仪表盘"], ...]

登录态要点（实测）：
- 前端多为 pinia-persistedstate，localStorage key 常为 store id（如 user）。
- 注入的 userInfo 必须带 /info 返回的 menus，否则左侧导航不渲染。
- /info 只带 X-Tkn 即可；多余 header 可能 502。
- agent-browser daemon 可能反复挂起；直接用 Python Playwright 指定系统 Chrome，
  可绕开 ms-playwright 缓存版本与新装 playwright 不匹配的问题。
- 验证码从 GET /api/v1/code 取 uuid + base64 图片，用 ViewImage 读出后 POST /signin。
"""
import argparse
import json
import os
import re

from playwright.sync_api import sync_playwright


def main():
    ap = argparse.ArgumentParser(description="批量截取系统界面")
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pages", required=True)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--info-file", required=True)
    ap.add_argument("--chrome", default=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    ap.add_argument("--storage-key", default="user")
    ap.add_argument("--login-path", default="")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=1000)
    ap.add_argument("--wait", type=int, default=2600)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tok = open(a.token_file, encoding="utf-8").read().strip()
    info = json.load(open(a.info_file, encoding="utf-8"))["data"]
    pages = json.load(open(a.pages, encoding="utf-8"))

    report = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=a.chrome,
                                     args=["--no-sandbox", "--disable-dev-shm-usage"])
        if a.login_path:
            anon = browser.new_context(viewport={"width": a.width, "height": a.height})
            lp = anon.new_page()
            lp.goto(a.base + a.login_path, wait_until="domcontentloaded", timeout=30000)
            lp.wait_for_timeout(2200)
            lp.screenshot(path=os.path.join(a.out, "00_login.png"), full_page=True)
            print("saved 00_login.png (登录页，注意后续需打码验证码)")
            anon.close()

        ctx = browser.new_context(viewport={"width": a.width, "height": a.height},
                                  device_scale_factor=1)
        state = json.dumps({"token": tok, "userInfo": info}, ensure_ascii=False)
        ctx.add_init_script("window.localStorage.setItem(%s, %s);"
                            % (json.dumps(a.storage_key), json.dumps(state)))
        page = ctx.new_page()
        for name, path, title in pages:
            try:
                page.goto(a.base + path, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(a.wait)
                img = os.path.join(a.out, name + ".png")
                page.screenshot(path=img, full_page=True)
                head = re.sub(r"\s+", " ", page.inner_text("body"))[:200]
                report.append({"name": name, "path": path, "title": title,
                               "url": page.url, "head": head})
                print("%-22s %5dKB  %s" % (name, os.path.getsize(img) // 1024, title))
            except Exception as e:
                report.append({"name": name, "path": path, "error": str(e)[:200]})
                print("%-22s ERROR %s" % (name, str(e)[:120]))
        browser.close()
    json.dump(report, open(os.path.join(a.out, "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("截图完成 ->", a.out)


if __name__ == "__main__":
    main()
