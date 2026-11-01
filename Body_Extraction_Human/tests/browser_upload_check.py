"""Submit a new file through the real UI and wait for actual worker output."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
P=Path(__file__).resolve().parents[1]
secret=dict(line.split('=',1) for line in (P/'.runtime/app.env').read_text().splitlines() if '=' in line)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8038/');page.get_by_label('ชื่อผู้ใช้').fill(secret['BODY_USERNAME']);page.get_by_label('รหัสผ่าน').fill(secret['BODY_PASSWORD']);page.get_by_role('button',name='เข้าสู่ระบบ',exact=True).click()
    page.get_by_role('heading',name='อัปโหลดและวิเคราะห์',exact=True).wait_for()
    page.locator('input[type=file]').set_input_files({'name':'broken-preview.png','mimeType':'image/png','buffer':b'broken'})
    page.get_by_text('เปิดภาพนี้ไม่ได้ หรือไฟล์ภาพเสีย',exact=True).wait_for();assert page.get_by_role('button',name='ส่งวิเคราะห์',exact=True).is_disabled()
    page.locator('input[type=file]').set_input_files(P/'.runtime/verification/empty.png')
    page.get_by_label('ชื่อแหล่งข้อมูล / กล้อง').fill('Browser verification')
    page.get_by_role('button',name='ส่งวิเคราะห์',exact=True).click()
    page.get_by_role('heading',name='empty.png',exact=True).wait_for()
    page.get_by_role('heading',name='ไม่พบบุคคลในเฟรมนี้',exact=True).wait_for(timeout=90000)
    page.wait_for_function('document.fonts.status === "loaded"')
    page.screenshot(path=str(P/'.runtime/browser/empty-result.png'),full_page=True)
    assert not errors,errors
    job=page.url.split('job=')[1].split('&')[0]
    result=dict(frontend_corrupt_preview_rejected=True,actual_UI_upload_to_worker=True,zero_person_success=True,job_id=job,JS_errors=errors)
    (P/'.runtime/verification/BROWSER_UPLOAD.json').write_text(json.dumps(result,indent=2));browser.close()
print(json.dumps({k:v for k,v in result.items() if k!='job_id'}))
