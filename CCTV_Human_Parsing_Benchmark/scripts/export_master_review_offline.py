"""Export a private, single-file GT viewer: no JS, server paths or SVG required.

RGB and annotation preview rasters are embedded. These downscaled visualizations
are not evaluation masks; the bound GT packets are read-only and unchanged.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import base64
import hashlib
import html
import io
import json

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
COLORS = [(150, 150, 150), (239, 85, 85), (0, 191, 219), (118, 212, 0), (180, 108, 255)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def preview(rgb, annotation, box=None):
    original = np.array(rgb.convert("RGB"))
    painted = original.copy()
    for shape in annotation["shapes"]:
        if shape["label"] in ("bbox", "person"):
            continue
        cv2.fillPoly(painted, [np.asarray(shape["points"], np.int32)],
                     COLORS[shape["group_id"] % len(COLORS)])
    painted = cv2.addWeighted(original, .64, painted, .36, 0)
    for shape in annotation["shapes"]:
        if shape["label"] == "bbox":
            continue
        points = np.asarray(shape["points"], np.int32)
        color = COLORS[shape["group_id"] % len(COLORS)]
        cv2.polylines(painted, [points], True, color, 2 if shape["label"] == "person" else 1)
        if shape["label"] != "person":
            x, y = points[0]
            cv2.putText(painted, f"{shape['group_id']}:{shape['label']}", (x, max(12, y)),
                        cv2.FONT_HERSHEY_SIMPLEX, .45, (255, 255, 255), 1, cv2.LINE_AA)
    image = Image.fromarray(painted)
    if box:
        image = image.crop(box)
    image.thumbnail((1280, 1280))
    return image


def jpeg(image):
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=84, optimize=True)
    return buffer.getvalue()


def embedded(image, alt):
    data = jpeg(image)
    encoded = base64.b64encode(data).decode("ascii")
    return (f'<img loading="lazy" width="{image.width}" height="{image.height}" '
            f'alt="{html.escape(alt)}" src="data:image/jpeg;base64,{encoded}">')


def export(revision, output):
    if output.exists():
        raise FileExistsError("Use a fresh viewer filename; preserve earlier exports")
    if output.parent.resolve() != revision.resolve():
        raise ValueError("Keep the private viewer inside its owning GT revision")
    sample = output.with_name("owner_repairs_before_after.jpg")
    if sample.exists():
        raise FileExistsError("Preserve earlier visual exports")
    bindings = read(revision / "PRIVATE_BINDINGS.json")
    font = WORKSPACE / "Human_Parsing_CCIHP_10_Image_Pilot/web/fonts/NotoSansThai.ttf"
    font_css = ""
    if font.is_file():
        font_css = '@font-face{font-family:ReviewThai;src:url(data:font/ttf;base64,' + base64.b64encode(font.read_bytes()).decode() + ')}'
    header = '''<!doctype html><html lang="th"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CCTV GT — ภาพก่อนและหลังแก้ ครบ 90 ภาพ</title><style>__FONT__
body{font:16px ReviewThai,Tahoma,system-ui;background:#f1f6f8;color:#193c4a;max-width:1500px;margin:auto;padding:20px}
header,details{background:white;padding:18px;border:1px solid #d9e4e8;border-radius:12px;margin:14px 0}
summary{cursor:pointer;font-weight:700;padding:8px}p{line-height:1.65}.panels{display:grid;grid-template-columns:1fr 1fr;gap:16px}
img{display:block;width:100%;height:auto;background:#eef2f4}.warning{color:#8b4a00}.index{display:flex;flex-wrap:wrap;gap:8px}.index a{padding:5px;color:#00766e}
small{color:#526c77}.zoom img{max-height:420px;object-fit:contain}a{color:#00766e}
@media(max-width:850px){.panels{grid-template-columns:1fr}}
</style><header><h1>GT CCTV: ก่อนและหลังแก้เจ้าของชิ้นส่วน</h1>
<p><b>ครบ 90 ภาพ • 127 คน • แก้ owner ที่ยืนยันแล้ว 2 จุด</b><br>
ไฟล์นี้ฝังภาพไว้แล้ว เปิดไฟล์เดียวได้โดยไม่ต้องใช้ server หรือ JavaScript กดหัวข้อของแต่ละภาพเพื่อเปิด/ปิด</p>
<p>สีแยกตามคน: <span style="color:#ef5555">คน 1 แดง</span> · <span style="color:#00a6be">คน 2 ฟ้า</span> · <span style="color:#548d00">คน 3 เขียว</span> · <span style="color:#9759df">คน 4 ม่วง</span>
เส้นแสดง person polygon และพื้นสีแสดง parts ของเจ้าของคนนั้น</p>
<p class="warning">นี่คือภาพตรวจ GT ไม่ใช่ผลโมเดล ยังรอตรวจความครบของ annotation และขอบเขตบางส่วน ไม่ใช่คะแนนใหม่</p>
<small>ภาพพรีวิวลดขนาดด้านยาวไม่เกิน 1280 px; masks/NPZ/annotation ต้นฉบับไม่เปลี่ยน ภาพนี้ใช้เพื่อเปิดตรวจด้วยตา</small></header><nav class="index">__INDEX__</nav><main>'''
    links = ''.join(f'<a href="#{html.escape(f["image_id"])}">{html.escape(f["image_id"])}</a>' for f in bindings["frames"])
    chunks = [header.replace("__FONT__", font_css).replace("__INDEX__", links)]
    originals, proof, sample_rows = {}, [], []
    owner_issues = bindings["owner_corrections"]
    for frame in bindings["frames"]:
        revised_path = WORKSPACE / frame["annotation"]
        if sha(revised_path) != frame["annotation_sha256"]:
            raise ValueError("Bound annotation changed")
        revised = read(revised_path)
        source = WORKSPACE / "datasets/CCTV_100_Evaluation/Annotations_Master" / revised_path.name
        rgb_path = (revised_path.parent / revised["imagePath"]).resolve()
        for path in [source, rgb_path]:
            rel = str(path.relative_to(WORKSPACE))
            if sha(path) != bindings["inputs"][rel]:
                raise ValueError("Source annotation/image changed")
            originals[rel] = bindings["inputs"][rel]
        before = read(source)
        with Image.open(rgb_path) as opened:
            rgb = opened.convert("RGB")
        iid = frame["image_id"]
        changes = [c for c in owner_issues if c["image_id"] == iid]
        note = ' / '.join(c["issue_id"] + ': ' + c["source_label"] + ' → ' + c["corrected_label"] for c in changes)
        if not note:
            note = "ไม่มีการเปลี่ยน owner ในภาพนี้; ยังต้องตรวจ coverage/ขอบเขต"
        left, right = preview(rgb, before), preview(rgb, revised)
        opened = " open" if iid == bindings["frames"][0]["image_id"] or changes else ""
        chunks.append(f'<details id="{html.escape(iid)}"{opened}><summary>{html.escape(iid)} — '+
            ('แก้ owner แล้ว' if changes else 'ตรวจ annotation') + '</summary><p>'+html.escape(note)+
            '</p><div class="panels"><section><h2>Master เดิม</h2>'+embedded(left,iid+' Master เดิม')+
            '</section><section><h2>ฉบับแก้</h2>'+embedded(right,iid+' ฉบับแก้')+'</section></div>')
        if changes:
            issue = changes[0]
            old_points = read(WORKSPACE / "datasets/CCTV_100_Evaluation/Annotations_canonical" / revised_path.name)
            # Exact changed contour from the existing reviewed correction record.
            rp = read(ROOT / "outputs/controlled-gt-owner-20261101/GT_REVISION.json")
            ref = next(r for r in rp["corrections"] if r["issue_id"] == issue["issue_id"])
            points = np.asarray(old_points["shapes"][ref["shape_index"]]["points"])
            x0,y0 = np.floor(points.min(axis=0)-35).astype(int)
            x1,y1 = np.ceil(points.max(axis=0)+35).astype(int)
            box=(max(0,x0),max(0,y0),min(rgb.width,x1+1),min(rgb.height,y1+1))
            zl,zr=preview(rgb,before,box),preview(rgb,revised,box)
            chunks.append('<h3>ขยายจุดที่แก้</h3><div class="panels zoom"><section>'+embedded(zl,iid+' ขยายก่อนแก้')+
                          '</section><section>'+embedded(zr,iid+' ขยายหลังแก้')+'</section></div>')
            sample_rows.append((iid,zl,zr))
        chunks.append('</details>')
        proof.append(dict(image_id=iid, source_RGB_sha256=sha(rgb_path), revised_annotation_sha256=sha(revised_path)))
    chunks.append('</main><footer><p>ข้อมูลครบ 90 ภาพในไฟล์นี้ ไม่มีการเรียกผลโมเดลหรือเว็บไซต์ภายนอก และไม่มีการสร้างคะแนนใหม่</p></footer></html>')
    output.write_text(''.join(chunks))
    # Directly viewable image fallback for clients that do not render HTML files.
    canvas = Image.new("RGB",(1200,len(sample_rows)*460),"white")
    font_object = ImageFont.truetype(str(font),22) if font.is_file() else ImageFont.load_default()
    draw = ImageDraw.Draw(canvas)
    for i,(iid,left,right) in enumerate(sample_rows):
        draw.text((20,i*460+8),iid+" — ก่อนแก้ / หลังแก้ (สีแยกตามคน)",font=font_object,fill="#193c4a")
        for j,image in enumerate([left,right]):
            factor=min(560/image.width,390/image.height)
            image=image.resize((round(image.width*factor),round(image.height*factor)),Image.Resampling.NEAREST)
            canvas.paste(image,(20+j*600,i*460+55))
    canvas.save(sample,quality=92)
    for name,checksum in originals.items():
        if sha(WORKSPACE/name)!=checksum:
            raise ValueError("Source input changed during export")
    result=dict(status="EXPORTED",created_utc=datetime.now(timezone.utc).isoformat(),frames=len(proof),
        file=str(output.relative_to(WORKSPACE)),sha256=sha(output),bytes=output.stat().st_size,
        javascript_required=False,external_images_required=False,external_fonts_required=False,
        preview_max_dimension=1280,JPEG_quality=84,GT_packets_modified=False,inference_calls=0,
        sample=str(sample.relative_to(WORKSPACE)),sample_sha256=sha(sample),source_sha256=sha(Path(__file__)),frames_bound=proof)
    output.with_suffix('.manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=export(args.revision.resolve(),args.output.resolve())
    print(json.dumps({k:v for k,v in result.items() if k!='frames_bound'},ensure_ascii=False,indent=2))
