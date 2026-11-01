"""Check real saved results, bidirectional selection and search deep links."""

from pathlib import Path
import json
from playwright.sync_api import sync_playwright

P = Path(__file__).resolve().parents[1]
secret = dict(
    line.split("=", 1)
    for line in (P / ".runtime/app.env").read_text().splitlines()
    if "=" in line
)
data = json.loads((P / ".runtime/verification/RUNNING.json").read_text())
jid = data["cases"]["multi.png"]["job_id"]
out = P / ".runtime/browser"
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1500, "height": 1050})
    r = context.request.post(
        "http://127.0.0.1:8038/api/login",
        data={"username": secret["BODY_USERNAME"], "password": secret["BODY_PASSWORD"]},
    )
    assert r.ok
    job = context.request.get("http://127.0.0.1:8038/api/jobs/" + jid).json()
    fid = job["frames"][0]["id"]
    f = context.request.get("http://127.0.0.1:8038/api/frames/" + fid).json()
    assert len(f["persons"]) >= 2
    selected = f["persons"][1]
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(
        "http://127.0.0.1:8038/#" + f"job={jid}&frame={fid}&person={selected['id']}"
    )
    page.get_by_alt_text("ภาพบุคคล 2").wait_for()
    page.wait_for_function(
        "Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)"
    )
    assert page.locator(".person-tabs .active").inner_text() == "#2"
    page.screenshot(path=str(out / "result.png"), full_page=True)
    page.locator(".person-box").first.click(position={"x": 20, "y": 20}, force=True)
    assert page.locator('.person-tabs .active').inner_text()=='#1'
    page.locator(".person-tabs button").first.click()
    page.get_by_alt_text("ภาพบุคคล 1").wait_for()
    page.reload()
    page.get_by_alt_text("ภาพบุคคล 1").wait_for()
    page.get_by_role("button", name="ประวัติและค้นหาบุคคล", exact=True).click()
    page.get_by_role("heading", name="ค้นหาจากลักษณะเสื้อผ้า", exact=True).wait_for()
    page.locator(".search-result").first.wait_for()
    page.locator(".search-result").first.click()
    page.locator(".person-crop").wait_for()
    assert "person=" in page.url
    clip=data['cases']['clip.mp4']['job_id']
    page.goto('http://127.0.0.1:8038/#job='+clip)
    page.locator('.video-bar select').wait_for();page.locator('.video-bar select').select_option(index=1)
    page.get_by_role('button',name='เปิดคลิป ณ เวลาที่พบ',exact=True).click()
    page.wait_for_function('document.querySelector("video")?.readyState >= 1')
    page.wait_for_function('Math.abs(document.querySelector("video").currentTime-1)<.3')
    page.locator('video').evaluate('(v)=>v.pause()')
    page.locator('.video-bar select').select_option(index=2)
    page.wait_for_function('Math.abs(document.querySelector("video").currentTime-2)<.15')
    page.screenshot(path=str(out/'video.png'),full_page=True)
    assert not errors, errors
    browser.close()
print(
    json.dumps(
        dict(
            real_result_images=True,
            person_deep_link=True,
            person_selection=True,
            refresh_preserves_person=True,
            search_opens_exact_person=True,
            video_frame_selection_and_seek=True,
            JS_errors=errors,
        )
    )
)
