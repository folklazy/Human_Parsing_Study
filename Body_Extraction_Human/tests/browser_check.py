"""Real Chromium UI checks. Private screenshots are never published."""

from pathlib import Path
import json, os
from playwright.sync_api import sync_playwright

P = Path(__file__).resolve().parents[1]
secret = dict(
    line.split("=", 1)
    for line in (P / ".runtime/app.env").read_text().splitlines()
    if "=" in line
)
out = P / ".runtime/browser"
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page(
        viewport={"width": 1440, "height": 1000}, device_scale_factor=1
    )
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:8038/")
    page.get_by_label("ชื่อผู้ใช้").fill(secret["BODY_USERNAME"])
    page.get_by_label("รหัสผ่าน").fill(secret["BODY_PASSWORD"])
    page.get_by_role("button", name="เข้าสู่ระบบ", exact=True).click()
    page.get_by_role("heading", name="อัปโหลดและวิเคราะห์", exact=True).wait_for()
    page.locator("input[type=file]").set_input_files(
        P / ".runtime/verification/multi.png"
    )
    page.get_by_alt_text("ตัวอย่างไฟล์ที่เลือก").wait_for()
    page.screenshot(path=str(out / "upload.png"), full_page=True)
    page.get_by_role("button", name="ประวัติและค้นหาบุคคล", exact=True).click()
    page.get_by_role("heading", name="ค้นหาจากลักษณะเสื้อผ้า", exact=True).wait_for()
    page.screenshot(path=str(out / "search.png"), full_page=True)
    page.reload()
    page.get_by_role("heading", name="ค้นหาจากลักษณะเสื้อผ้า", exact=True).wait_for()
    assert not errors, errors
    browser.close()
print(
    json.dumps(
        dict(
            browser="Chromium",
            login=True,
            upload_preview=True,
            search_page=True,
            refresh_session=True,
            JS_errors=errors,
        )
    )
)
