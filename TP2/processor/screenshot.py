from __future__ import annotations

import io
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


def _placeholder_png(url: str, width: int = 1024, height: int = 640) -> bytes:
    img = Image.new("RGB", (width, height), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    text = f"Screenshot placeholder\n{url}"
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.multiline_text((20, 20), text, fill=(220, 220, 220), font=font, spacing=6)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def take_screenshot(url: str, width: int = 1024, height: int = 640) -> bytes:
    # Intentar usar Playwright o Selenium si estuvieran disponibles; caso contrario, placeholder
    try:
        from playwright.sync_api import sync_playwright  # type: ignore

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()
            page.goto(url, timeout=30000, wait_until="networkidle")
            png = page.screenshot(full_page=True)
            browser.close()
            return png
    except Exception:
        pass

    try:
        from selenium import webdriver  # type: ignore
        from selenium.webdriver.chrome.options import Options  # type: ignore

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument(f"--window-size={width},{height}")
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        driver.get(url)
        png = driver.get_screenshot_as_png()
        driver.quit()
        return png
    except Exception:
        return _placeholder_png(url, width, height)

