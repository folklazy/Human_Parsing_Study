"""Derive auditable CCTV masks from Master; never infer missing GT labels.

No parser/model outputs are read. This prepares annotation candidates, not scores
or a frozen CIHP-equivalent evaluation domain. Original datasets stay immutable.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse
import copy
import csv
import hashlib
import io
import json
import os

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
TARGETS = {"face": 1, "hair": 2, "upper": 3, "lower": 4}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def atomic_json(path, value):
    atomic_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def semantic_signature(annotation):
    return sorted((f"p{s['group_id']}_{s['label']}", s["points"])
                  for s in annotation["shapes"] if s["label"] in TARGETS)


def correct_owners(master, canonical, issues):
    """Identify reviewed shapes by original label AND vertices, never proximity."""
    expected = sorted((s["label"], s["points"]) for s in canonical["shapes"])
    if semantic_signature(master) != expected:
        raise ValueError("Master semantic annotations changed; reconcile before applying old fixes")
    result = copy.deepcopy(master)
    changes = []
    for issue in issues:
        source = canonical["shapes"][issue["shape_index"]]
        if source["label"] != issue["source_label"]:
            raise ValueError("Reviewed canonical shape binding differs")
        matches = [s for s in result["shapes"] if s["label"] in TARGETS
                   and f"p{s['group_id']}_{s['label']}" == source["label"]
                   and s["points"] == source["points"]]
        if len(matches) != 1:
            raise ValueError("Reviewed polygon is missing or ambiguous")
        pid, target = issue["proposed_label"].split("_")
        shape = matches[0]
        if target != shape["label"]:
            raise ValueError("Owner repair may not change target or contour")
        shape["group_id"] = int(pid[1:])
        shape.setdefault("attributes", {}).update(person_id=pid, instance_id=int(pid[1:]))
        changes.append({"issue_id": issue["issue_id"], "source_label": issue["source_label"],
                        "corrected_label": issue["proposed_label"], "vertices_changed": False})
    for shape in result["shapes"]:
        attr = shape.setdefault("attributes", {})
        if shape["label"] in TARGETS:
            # A source metadata claim is not evidence of pixel-boundary equivalence.
            if "cihp_equivalent_classes" in attr:
                attr["source_claimed_cihp_equivalent_classes"] = attr.pop("cihp_equivalent_classes")
            attr["CIHP_boundary_equivalence"] = "NOT_CERTIFIED"
        elif shape["label"] == "person":
            attr["annotated_parts"] = sorted({f"p{shape['group_id']}_{s['label']}"
                for s in result["shapes"] if s["label"] in TARGETS
                and s["group_id"] == shape["group_id"]})
    return result, changes


def polygon_mask(shape, height, width):
    points = np.asarray(shape["points"], dtype=np.float64)
    if points.ndim != 2 or points.shape[1:] != (2,) or len(points) < 3 or not np.isfinite(points).all():
        raise ValueError("Malformed polygon")
    if ((points < 0).any() or (points[:, 0] > width).any()
            or (points[:, 1] > height).any()):
        raise ValueError("Polygon exceeds closed image-edge coordinates")
    result = np.zeros((height, width), np.uint8)
    # This reproduces the historical semantic rasterizer. Coordinates at W/H
    # are image edges; OpenCV clips to the grid. Never use rounding or a bbox fill.
    cv2.fillPoly(result, [points.astype(np.int32)], 1)
    return result.astype(bool)


def raster_candidates(annotation):
    h, w = annotation["imageHeight"], annotation["imageWidth"]
    ids = sorted({s["group_id"] for s in annotation["shapes"] if s["label"] == "person"})
    if not ids or any(type(i) is not int or not 0 < i < 255 for i in ids):
        raise ValueError("Person IDs must be distinct positive integers below reserved 255")
    extents = {pid: np.zeros((h, w), bool) for pid in ids}
    parts = {}
    for shape in annotation["shapes"]:
        label = shape["label"]
        if label == "bbox":
            continue  # Annotation bboxes must never replace parser/YOLO inputs.
        if label not in TARGETS and label != "person":
            raise ValueError("Unknown annotation label")
        if shape.get("shape_type") != "polygon" or shape["group_id"] not in extents:
            raise ValueError("Part owner or polygon contract invalid")
        mask = polygon_mask(shape, h, w)
        if label == "person":
            extents[shape["group_id"]] |= mask
        else:
            key = (shape["group_id"], TARGETS[label])
            parts.setdefault(key, np.zeros((h, w), bool))
            parts[key] |= mask
    masks = np.stack([extents[pid] for pid in ids])
    if any(not mask.any() for mask in masks):
        raise ValueError("Empty person extent")
    overlap = masks.sum(axis=0) > 1
    owner = np.zeros((h, w), np.uint8)
    for pid, mask in zip(ids, masks):
        owner[mask] = pid
    owner[overlap] = 255  # Do not silently decide visibility from numeric ID/order.
    keys = sorted(parts)
    part_masks = np.stack([parts[k] for k in keys]) if keys else np.zeros((0, h, w), bool)
    outside = sum(int((parts[k] & ~extents[k[0]]).sum()) for k in keys)
    candidate = np.full((h, w), 255, np.uint8)
    semantic_overlap = part_masks.sum(axis=0) > 1
    for key in keys:
        candidate[parts[key]] = key[1]
    candidate[semantic_overlap] = 255
    return dict(person_ids=np.asarray(ids, np.uint8), person_masks=masks,
                person_id_candidate=owner, person_overlap=overlap,
                part_person_ids=np.asarray([k[0] for k in keys], np.uint8),
                part_target_ids=np.asarray([k[1] for k in keys], np.uint8), part_masks=part_masks,
                semantic_candidate=candidate, semantic_overlap=semantic_overlap), outside


def write_gallery(output, records):
    """Private file:// viewer; embedded annotations avoid fetch/CORS failures."""
    data = json.dumps(records, ensure_ascii=False).replace("<", "\\u003c")
    html = '''<!doctype html><html lang="th"><meta charset="utf-8">
<title>CCTV — ตรวจ GT ฉบับแก้</title><style>
body{font:16px system-ui;background:#f2f6f8;color:#193c4a;margin:24px}
header,section{background:white;border-radius:12px;padding:18px;margin-bottom:16px}
select,button{padding:8px;margin:5px} .panels{display:grid;grid-template-columns:1fr 1fr;gap:16px}
svg{width:100%;background:#ddd}p{line-height:1.6}.note{color:#8c4f00}
</style><header><h1>ตรวจ GT CCTV: ก่อนและหลังแก้เจ้าของชิ้นส่วน</h1>
<p>สีแยกตามหมายเลขคน เส้นคือ person polygon; พื้นสีคือชิ้นส่วนที่ annotate ไว้
ภาพนี้เป็น GT ไม่ใช่ผลโมเดล และยังไม่รับรองว่า annotate ทุกส่วนครบ</p>
<button id="prev">ก่อนหน้า</button><select id="choose"></select><button id="next">ถัดไป</button>
<label><input type="checkbox" id="parts" checked>แสดงชิ้นส่วน</label>
<p class="note" id="note"></p></header><main class="panels">
<section><h2>Master เดิม</h2><div id="before"></div></section>
<section><h2>ฉบับแก้ (ยังรอตรวจ coverage)</h2><div id="after"></div></section></main>
<script>const records=__DATA__,ns='http://www.w3.org/2000/svg';
const colors=['#aaa','#ef5555','#00bfdb','#76d400','#b46cff','#ffae00'];
const select=document.getElementById('choose');
records.forEach((r,i)=>{let o=document.createElement('option');o.value=i;o.textContent=r.id+(r.changes.length?' — แก้ owner':'');select.append(o)});
function panel(r,field){let svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${r.width} ${r.height}`);
let im=document.createElementNS(ns,'image');im.setAttribute('href',r.image);im.setAttribute('width',r.width);im.setAttribute('height',r.height);svg.append(im);
r[field].forEach(s=>{if(s.label==='bbox'||(!document.getElementById('parts').checked&&s.label!=='person'))return;
let p=document.createElementNS(ns,'polygon');p.setAttribute('points',s.points.map(x=>x.join(',')).join(' '));let c=colors[s.group_id%colors.length];
p.setAttribute('stroke',c);p.setAttribute('stroke-width',s.label==='person'?2:1);p.setAttribute('fill',s.label==='person'?'none':c);p.setAttribute('fill-opacity','.38');
let title=document.createElementNS(ns,'title');title.textContent=`คน ${s.group_id}: ${s.label}`;p.append(title);svg.append(p);
if(s.label!=='person'){let t=document.createElementNS(ns,'text');t.setAttribute('x',s.points[0][0]);t.setAttribute('y',s.points[0][1]);t.setAttribute('fill','white');t.setAttribute('stroke','#111');t.setAttribute('stroke-width','.5');t.setAttribute('font-size','16');t.textContent=`${s.group_id}:${s.label}`;svg.append(t)}});
document.getElementById(field).replaceChildren(svg)}
function render(){let r=records[Number(select.value)];panel(r,'before');panel(r,'after');document.getElementById('note').textContent=r.changes.length?r.changes.map(c=>c.issue_id+': '+c.source_label+' → '+c.corrected_label).join(' / '):'ไม่เปลี่ยน owner/ขอบเขตของภาพนี้; การไม่มี polygon ไม่ได้หมายความว่าส่วนนั้นไม่ปรากฏ'}
select.onchange=render;document.getElementById('parts').onchange=render;
document.getElementById('prev').onclick=()=>{select.value=Math.max(0,+select.value-1);render()};document.getElementById('next').onclick=()=>{select.value=Math.min(records.length-1,+select.value+1);render()};render();
</script></html>'''.replace("__DATA__", data)
    atomic_bytes(output / "index.html", html.encode())


def prepare(output):
    if not output.resolve().is_relative_to((ROOT / "outputs").resolve()):
        raise ValueError("Revision output must belong to this experiment's outputs")
    output.mkdir(parents=True, exist_ok=False)
    try:
        dataset = WORKSPACE / "datasets/CCTV_100_Evaluation"
        source = dataset / "Annotations_Master"
        cp = ROOT / "outputs/cctv-partial-20261031T1800Z/CONFIG.json"
        rp = ROOT / "outputs/controlled-gt-owner-20261101/GT_REVISION.json"
        parent, revision = read(cp), read(rp)
        expected = {m["stem"] for m in parent["members"]}
        if len(expected) != 90 or len(parent["members"]) != 90:
            raise ValueError("Frozen population must contain 90 unique image members")
        if {p.stem for p in source.glob("*.json")} != expected:
            raise ValueError("Master image membership differs from frozen cohort")
        prior = read(ROOT / "outputs/controlled-gt-screen-20261101-bound/GT_BINDING.json")
        prior_parts = {(r["image_id"], r["person_id"], r["source_target"].lower()): r
                       for r in prior["part_records"]}
        frames, review, all_changes, inputs, gallery = [], [], [], {}, []
        total = Counter()
        for member in parent["members"]:
            iid, stem = member["id"], member["stem"]
            path = source / (stem + ".json")
            canonical_path = dataset / "Annotations_canonical" / path.name
            rgb = dataset / "Images" / (stem + ".jpg")
            old_png = dataset / "Full_Person_ids" / (stem + ".png")
            if sha(canonical_path) != member["annotation_sha256"] or sha(rgb) != member["RGB_sha256"]:
                raise ValueError("Canonical annotation or image binding changed")
            for p in [path, canonical_path, rgb, old_png]:
                inputs[str(p.relative_to(WORKSPACE))] = sha(p)
            issues = [r for r in revision["corrections"] if r["image_id"] == iid]
            master = read(path)
            if Image.open(rgb).size != (master["imageWidth"], master["imageHeight"]):
                raise ValueError("Image and annotation dimensions differ")
            corrected, changes = correct_owners(master, read(canonical_path), issues)
            arrays, outside = raster_candidates(corrected)
            corrected["imagePath"] = os.path.relpath(rgb, output / "Annotations_Reviewed")
            corrected["annotation_revision"] = {"status": "DERIVED_MECHANICAL_REPAIR_REVIEW_PENDING",
                "source_sha256": inputs[str(path.relative_to(WORKSPACE))],
                "owner_corrections": changes, "global_coverage_verified": False,
                "source_contours_preserved": True, "no_parser_predictions_used": True}
            ap = output / "Annotations_Reviewed" / path.name
            atomic_json(ap, corrected)
            npz = output / "packets" / (iid + ".npz")
            buffer = io.BytesIO()
            np.savez_compressed(buffer, **arrays)
            atomic_bytes(npz, buffer.getvalue())
            png = output / "Full_Person_ids" / (stem + ".png")
            buffer = io.BytesIO()
            Image.fromarray(arrays["person_id_candidate"]).save(buffer, format="PNG")
            atomic_bytes(png, buffer.getvalue())
            with np.load(npz, allow_pickle=False) as saved:
                for key, value in arrays.items():
                    if not np.array_equal(saved[key], value):
                        raise ValueError("Atomic packet readback differs")
            if not np.array_equal(np.array(Image.open(png)), arrays["person_id_candidate"]):
                raise ValueError("PNG readback differs")
            for pid in arrays["person_ids"].tolist():
                for target, code in TARGETS.items():
                    found = np.where((arrays["part_person_ids"] == pid) & (arrays["part_target_ids"] == code))[0]
                    previous = prior_parts.get((iid, pid, target))
                    review.append(dict(image_id=iid, person_id=pid, target=target,
                        status="SOURCE_POSITIVE_COVERAGE_PENDING" if len(found) else "UNKNOWN_NO_POLYGON",
                        positive_pixels=int(arrays["part_masks"][found[0]].sum()) if len(found) else None,
                        confirmed_absent=False, CIHP_boundary_equivalence="NOT_CERTIFIED",
                        prior_selected_part_screen=previous.get("eligible") if previous else None,
                        prior_QA_reason=previous.get("QA_reason") if previous else None))
            all_changes.extend(dict(image_id=iid, **c) for c in changes)
            gallery.append(dict(id=iid, image=os.path.relpath(rgb, output), width=master["imageWidth"],
                height=master["imageHeight"], changes=changes,
                before=[{k: s[k] for k in ("label", "group_id", "points")} for s in master["shapes"]],
                after=[{k: s[k] for k in ("label", "group_id", "points")} for s in corrected["shapes"]]))
            total.update(images=1, persons=len(arrays["person_ids"]), parts=len(arrays["part_target_ids"]),
                         person_overlap_pixels=int(arrays["person_overlap"].sum()),
                         part_pixels_outside_own_extent=outside)
            frames.append(dict(image_id=iid, annotation=str(ap.relative_to(WORKSPACE)),
                annotation_sha256=sha(ap), packet=str(npz.relative_to(WORKSPACE)), packet_sha256=sha(npz),
                person_png=str(png.relative_to(WORKSPACE)), person_png_sha256=sha(png)))
            print(f"GT repair {len(frames)}/90; no model inference", flush=True) if len(frames) % 30 == 0 else None
        if len(all_changes) != len(revision["corrections"]):
            raise ValueError("Not all bound owner corrections applied")
        for name, checksum in inputs.items():
            if sha(WORKSPACE / name) != checksum:
                raise ValueError("Input changed during preparation")
        atomic_json(output / "PRIVATE_BINDINGS.json", {"inputs": inputs, "frames": frames,
            "owner_corrections": all_changes, "source_config_sha256": sha(cp), "owner_revision_sha256": sha(rp)})
        atomic_json(output / "REVIEW_QUEUE.json", {"status": "COVERAGE_AND_BOUNDARY_REVIEW_PENDING", "rows": review})
        with (output / "REVIEW_QUEUE.csv").open("x", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(review[0]))
            writer.writeheader()
            writer.writerows(review)
        write_gallery(output, gallery)
        result = dict(status="MECHANICAL_REPAIR_COMPLETE_REVIEW_PENDING", created_utc=datetime.now(timezone.utc).isoformat(),
            artifact_root=str(output.relative_to(WORKSPACE)), counts=dict(total), owner_corrections=len(all_changes),
            source_sha256=sha(Path(__file__)), renderer=f"OpenCV {cv2.__version__}: float-to-int32 truncation, fillPoly",
            shape_coordinates="closed image edges [0,W]x[0,H]; raster clipped by OpenCV",
            representation="Per-person boolean extents authoritative for this candidate; PNG 255 means unresolved overlap",
            overlap_policy="Preserve all per-person polygons; require visibility review, never numeric-ID winner",
            outside_person_PNG_zero="outside annotated people; not certified semantic background",
            semantic_unknown=255, semantic_bg_other_invented=False, scoring_ready=False, primary=None,
            coverage_review_items=len(review), unknown_no_polygon=sum(r["status"] == "UNKNOWN_NO_POLYGON" for r in review),
            source_annotations_modified=False, source_contours_modified=False, model_inference_calls=0,
            expert_certified=False, private_binding_sha256=sha(output / "PRIVATE_BINDINGS.json"))
        atomic_json(output / "COMPLETION.json", result)
        return result
    except Exception as error:
        atomic_json(output / "FAILURE.json", {"status": "STOPPED", "error": str(error), "attempt_preserved": True})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output.resolve()), ensure_ascii=False))
