"""Real browser: saved video -> appearance filters -> moments -> exact frame/seek.

Uses accepted local QA outputs only. Does not upload or infer any new media.
"""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
P=Path(__file__).resolve().parents[1]
secret=dict(line.split('=',1) for line in (P/'.runtime/app.env').read_text().splitlines() if '=' in line)
evidence=json.loads((P/'.runtime/verification/RESULTS.json').read_text());jid=evidence['cases']['clip.mp4']['job_id']
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox']);context=browser.new_context(viewport={'width':1460,'height':1100})
    response=context.request.post('http://127.0.0.1:8038/api/login',data={'username':secret['BODY_USERNAME'],'password':secret['BODY_PASSWORD']});assert response.ok
    base=context.request.get('http://127.0.0.1:8038/api/search',params={'job_id':jid}).json()
    person=next(p for p in base['items'] if p['upper_colors'] and p['lower_colors'])
    upper,lower=person['upper_colors'][0],person['lower_colors'][0]
    expected=context.request.get('http://127.0.0.1:8038/api/search',params={'job_id':jid,'upper':upper,'lower':lower,'include_moments':'true'}).json()
    assert expected['moments']
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8038/#job='+jid)
    page.get_by_role('button',name='ค้นหาบุคคลในคลิปนี้',exact=True).click()
    picker=page.get_by_label('ขอบเขตวิดีโอ',exact=True)
    page.wait_for_function('(id)=>document.querySelector(".video-search-scope select")?.value===id',arg=jid)
    page.get_by_label('สีเสื้อผ้าส่วนบน',exact=True).select_option(upper)
    page.get_by_label('สีเสื้อผ้าส่วนล่าง',exact=True).select_option(lower)
    with page.expect_response(lambda r:'/api/search?' in r.url and 'upper=' in r.url and 'lower=' in r.url):
        page.get_by_role('button',name='ค้นหา',exact=True).click()
    page.get_by_role('heading',name=f"พบ {expected['total']} รายการบุคคล",exact=True).wait_for()
    page.wait_for_function('(n)=>document.querySelectorAll(".moment").length===n',arg=len(expected['moments']))
    page.wait_for_function('document.fonts.status === "loaded"')
    page.screenshot(path=str(P/'.runtime/browser/video-search.png'),full_page=True)
    last=expected['moments'][-1];selected=last['persons'][0]
    page.locator('.moment').last.locator('.moment-persons button').first.click()
    page.get_by_alt_text('ภาพบุคคล '+str(selected['ordinal']),exact=True).wait_for()
    assert 'frame='+last['frame_id'] in page.url and 'person='+selected['id'] in page.url
    frame=context.request.get('http://127.0.0.1:8038/api/frames/'+last['frame_id']).json();assert frame['timestamp_seconds']==last['timestamp_seconds']
    page.get_by_role('button',name='เปิดคลิป ณ เวลาที่พบ',exact=True).click()
    page.wait_for_function('(t)=>document.querySelector("video")?.readyState>=1 && Math.abs(document.querySelector("video").currentTime-t)<.3',arg=last['timestamp_seconds'])
    page.locator('video').evaluate('(v)=>v.pause()')
    assert not errors,errors
    result=dict(video_scope=True,same_person_AND_filters=True,moments=len(expected['moments']),exact_frame_person_link=True,actual_video_seek=True,JS_errors=errors,new_inference=False)
    (P/'.runtime/verification/VIDEO_SEARCH.json').write_text(json.dumps(result,indent=2));browser.close()
print(json.dumps(result))
