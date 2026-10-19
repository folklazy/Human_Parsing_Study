"""Publish the bounded Stage 0E findings with archived document revisions."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import difflib
import hashlib
import io
import json

ROOT = Path(__file__).resolve().parents[1]
active = json.loads((ROOT / 'provenance/CCIHP_STAGE0E_ACTIVE_RUN.json').read_text())
RUN = ROOT / active['run_path']
ARCHIVE = ROOT / 'reports/archive' / active['run_id']
NOW = datetime.now(timezone.utc).isoformat()
revisions = []
created = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def publish(name, text):
    path = ROOT / name
    if path.exists():
        original = path.read_text()
        backup = ARCHIVE / name
        backup.parent.mkdir(parents=True, exist_ok=True)
        with backup.open('x') as f:
            f.write(original)
        backup.with_name(backup.name + '.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), text.splitlines(True),
                                                                                fromfile=name+' BEFORE', tofile=name+' AFTER')))
        revisions.append({'original_relative': name, 'archived_relative': str(backup.relative_to(ROOT)),
                          'sha256_before': sha(path), 'sha256_after': hashlib.sha256(text.encode()).hexdigest(),
                          'reason': 'Stage 0E actual archive identity, missing person GT and compatibility evidence', 'timestamp_utc': NOW})
    else:
        created.append(name)
    tmp = path.with_name(path.name + '.tmp-' + active['run_id'])
    with tmp.open('x') as f:
        f.write(text)
    tmp.replace(path)


def save(name, value):
    publish(name, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


execution = json.loads((RUN / 'EXECUTION.json').read_text())
identity = json.loads((RUN / 'ARCHIVE_IDENTITY.json').read_text())
bounded = json.loads((RUN / 'CIHP_BOUNDED_REFERENCE_RECHECK.json').read_text())
prior = json.loads((ROOT / 'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json').read_text())
native = __import__('yaml').safe_load((ROOT / 'taxonomy/CIHP_NATIVE_SOURCE_INVENTORY_DRAFT.yaml').read_text())
card_path = RUN / 'sources/ccihp_author_view.json'
card = json.loads(card_path.read_text())
PAPER = 'https://arxiv.org/html/2201.09594v1#S2'
CARD = 'https://www.kaggle.com/datasets/angeliqueloesch/ccihp-characterized-crowd-instancelevel-hp'
rows = []
changes = {
    2: ('Hair incl. facial hair', 'INCOMPATIBLE', 'Published CCIHP expands hair to beard/mustache; original pixels cannot be reconstructed from coarse class alone'),
    4: ('Sunglasses/Glasses', 'INCOMPATIBLE', 'CCIHP covers broader eyewear than native sunglasses; same name/index does not imply same target'),
    5: ('UpperClothes incl. top of dress', 'AMBIGUOUS', 'Original Dress regions split into upper/lower garment targets; reverse native Dress requires source annotation'),
    6: ('Face Mask', 'INCOMPATIBLE', 'Native CIHP index 6 is Dress; author card position 6 is Face Mask; no native Dress category in stated CCIHP design'),
    11: ('Scarf incl. ties/bow ties', 'INCOMPATIBLE', 'CCIHP explicitly broadens neck clothing semantics'),
    12: ('Skirt incl. bottom of dress', 'AMBIGUOUS', 'CCIHP merges dress bottom with skirt; native garment identity is not recoverable without original labels')}
for class_id, label in native['labels'].items():
    concept, status, reason = changes.get(class_id, (label, 'NOT_VERIFIED', 'Similar documented concept only; no local CCIHP pixels or class IDs verified'))
    if class_id == 0:
        concept, status, reason = 'Background / ignore policy not verified from local CCIHP', 'NOT_VERIFIED', 'No CCIHP source masks; native background=0 does not establish CCIHP background/void or accessory coverage'
    rows.append({'cihp_native_id': class_id, 'cihp_native_name': label,
                 'ccihp_author_documented_position': class_id if class_id else 'UNVERIFIED',
                 'ccihp_documented_concept': concept, 'compatibility_status': status,
                 'evidence_scope': 'PUBLISHED_SEMANTICS_ONLY_NO_LOCAL_CCIHP',
                 'local_ccihp_pixel_verification': 'NOT_TESTED', 'reason': reason,
                 'source': PAPER if class_id in changes else CARD, 'mapping_frozen': False})
for position, concept in [(6, 'Face Mask'), (20, 'Bag'), (21, 'Others')]:
    rows.append({'cihp_native_id': 'NO_DISTINCT_NATIVE_CLASS', 'cihp_native_name': 'No distinct counterpart',
                 'ccihp_author_documented_position': position, 'ccihp_documented_concept': concept,
                 'compatibility_status': 'MISSING', 'evidence_scope': 'AUTHOR_CARD_ONLY_NOT_ARCHIVE_CLASS_ID',
                 'local_ccihp_pixel_verification': 'NOT_TESTED', 'reason': 'Native CIHP does not preserve this as a distinct semantic class; do not map unsupported GT to background',
                 'source': CARD, 'mapping_frozen': False})
stream = io.StringIO(newline='')
writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
writer.writeheader()
writer.writerows(rows)
publish('taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv', stream.getvalue())

facts = dict(schema_version='1.0', run_id=active['run_id'], timestamp_utc=NOW,
             requested_ccihp_archive='datasets/CCIHP_icip.zip', requested_ccihp_archive_present=False,
             user_identified_target='datasets/cihp-DatasetNinja.tar', actual_target_identity='CIHP_DATASETNINJA_CONVERSION_NOT_CCIHP',
             requested_ccihp_archive_bytes=None, requested_ccihp_archive_sha256=None,
             ccihp_crc_validation='NOT_TESTED_MISSING_ARCHIVE', ccihp_paths_validation='NOT_TESTED_MISSING_ARCHIVE',
             ccihp_local_train_count=None, ccihp_local_validation_count=None, ccihp_person_count=None,
             ccihp_human_ids_validation='BLOCKED_MISSING_SOURCE', ccihp_visual_inspection='NOT_TESTED',
             ccihp_native_equivalence='NOT_VERIFIED', ccihp_original_annotation_license='AUTHOR_DECLARED_CC_BY_NC_4_0_LOCAL_RELEASE_LICENSE_NOT_INSPECTED',
             actual_target_bytes=prior['archive_bytes'], actual_target_prior_sha256=prior['archive_sha256'],
             actual_target_whole_archive_rehashed=False, actual_target_bounded_payload_hashes='PASS',
             reused_complete_preflight='provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json',
             actual_target_train_images=prior['counts']['training_images'], actual_target_val_images=prior['counts']['validation_images'],
             actual_target_test_images=prior['counts']['testing_images'], actual_target_foreground_classes=19,
             actual_target_human_gt='MISSING', actual_target_foreground_semantic_reconstruction='PASS_5_NATIVE_DEMO_CASES_ONLY',
             fresh_native_demo_cases=5, fresh_semantic_pixel_differences=0, fresh_gt_visualizations=3,
             diagnostics_purpose='CIHP semantic-only reference parity; not CCIHP human-instance evidence',
             source_manifest=str((RUN / 'sources/SOURCE_MANIFEST.json').relative_to(ROOT)),
             author_card_sha256=sha(card_path), paper_semantic_changes='Verified published changes; not local release fidelity',
             documented_taxonomy_version_warning='Paper describes 19 foreground categories; author card claims 20 but enumerates 21 incl. Bag/Others; actual archive/version/code unavailable',
             matrix='taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv', taxonomy_frozen=False,
             decision='C', decision_name='NATIVE_CIHP_REQUIRED', decision_scope='CURRENTLY_AVAILABLE_ASSETS_ONLY',
             native_cihp_benchmark_gt_ready=False, custom_semantic_track='CONDITIONAL_QUALITY_AND_DATASET_RIGHTS_REVIEW',
             custom_person_instance_track='BLOCKED_NO_VERIFIED_PERSON_GT',
             native_asset_acquisition='RECOMMENDED_SUPPLEMENT_OR_DISTRIBUTION_NOT_AUTHORIZED',
             discovery=str((RUN / 'DISCOVERY.json').relative_to(ROOT)), identity_evidence=str((RUN / 'ARCHIVE_IDENTITY.json').relative_to(ROOT)),
             bounded_evidence=str((RUN / 'CIHP_BOUNDED_REFERENCE_RECHECK.json').relative_to(ROOT)),
             model_inference=False, checkpoint_download=False, dataset_download=False,
             original_dataset_modified=False, full_benchmark=False, ppss_activity=False, cctv_activity=False)
save('provenance/CCIHP_ARCHIVE_AUDIT.json', facts)
publish('reports/CCIHP_CIHP_COMPATIBILITY_AUDIT.md', f'''# Stage 0E — CCIHP / CIHP Native GT Compatibility Audit

**Stage 0E person-GT verification: BLOCKED. Decision C — NATIVE_CIHP_REQUIRED สำหรับ assets ที่มีอยู่ตอนนี้** ตรวจ source ตามที่ผู้ใช้ยืนยันจริง ไม่เริ่ม Stage 0 ใหม่ ไม่ download CIHP/CCIHP และไม่รัน parsing/attribute benchmark

## 1. ไฟล์จริงและความหมายของชื่อ dataset

ผู้ใช้ระบุ `datasets/cihp-DatasetNinja.tar` ว่าเป็น CCIHP แต่การอ่าน payload จริงยืนยันเป็น **CIHP DatasetNinja/Supervisely conversion** ไม่ใช่ CCIHP annotation release:

- Archive README ระบุ CIHP: Crowd Instance-level Human Parsing; LICENSE ระบุ CIHP/MIT
- `meta.json` มี **19 foreground labels** รวม `dress` และ `sunglasses`; ไม่มี Face Mask, Bag, Others
- Annotation เป็น per-image JSON + part bitmaps มี `classTitle`, object ID, bitmap origin; tags ว่าง ไม่มี person association
- Inventory เดิมครบ 76,563 regular members ไม่มี Category_ids/Human_ids/Instance_ids/Color_ids/Pattern_ids/Size_ids; **การไม่มี directories เพียงอย่างเดียวไม่ใช่ข้อพิสูจน์** แต่ metadata/schema/whole-JSON audit เดิมก็ไม่มี human grouping

ไม่พบ `datasets/CCIHP_icip.zip` หรือ CCIHP extracted source ใน workspace ที่ค้น รวม 620 directories ใน discovery แรก ค้นชื่อโดยไม่ลง environments/generated outputs/PPSS; ไม่อ้างว่าไฟล์บน Windows มีอยู่บน server [Actual payload identity]({('../' + str((RUN / 'ARCHIVE_IDENTITY.json').relative_to(ROOT)))})

| รายการ | CCIHP ที่ร้องขอ | TAR ที่มีจริง |
|---|---|---|
| Local availability | MISSING | PASS |
| Size | NOT_AVAILABLE | 2,015,375,360 bytes |
| SHA256 | NOT_AVAILABLE | `{prior['archive_sha256']}` **historical verified SHA** |
| ZIP central directory/CRC/safe paths | NOT_TESTED — source absent | ZIP checks ไม่ใช้กับ plain TAR; reuse verified TAR inventory |
| Train/Val/Test counts | Local counts NOT_TESTED | 28,280 / 5,000 / 5,000 |
| Person ground truth | NOT_TESTED | MISSING_NATIVE_HUMAN_OWNERSHIP_INFORMATION |

ไม่ rehash TAR ขนาด 2 GB ซ้ำ ใช้ inventory/annotation-summary cryptographic hashes เดิมที่ตรวจตรง และ reread 13 selected members **322,301 bytes** ทุก payload ตรง SHA256 เดิม ขอบเขตนี้ไม่อ้างว่า revalidated ทุก payload รอบใหม่

## 2. Native CIHP reference recheck ที่รันจริง

ตรวจ TRAIN demo IDs 0002190, 0005008, 0012008, 0026375, 0032190 จาก TAR เทียบ pinned official PGN RGB/semantic fixtures ที่ยังอยู่จริง RGB decode/pixels/bytes และ original-grid semantic maps ตรงกันทุกภาพ **semantic mismatch = 0 pixels; foreground/background mismatch = 0 pixels**

นี่คือ native **semantic-only reference** 5 ตัวอย่าง ไม่ใช่ full-release equivalence และไม่มี native Human_ids/part-instance reference ให้เทียบ อนุญาตให้ตรวจ validation counts จากหลักฐานเดิมได้ แต่ไม่มี validation model inference/tuning

[Bounded evidence](../{str((RUN / 'CIHP_BOUNDED_REFERENCE_RECHECK.json').relative_to(ROOT))}), [prior full preflight](CIHP_ARCHIVE_PREFLIGHT_AUDIT.md), [person verification](CCIHP_PERSON_INSTANCE_VERIFICATION.md)

## 3. CCIHP semantics ไม่ใช่ CIHP เดิม

**Verified published facts:** CCIHP paper §2 ระบุแก้ human masks และ semantic definitions, แยก Dress เข้า UpperClothes/Skirt, เพิ่ม facial-mask category, ขยาย hair/eyewear/neck clothing; human masks รวม accessories เพิ่ม จำนวนคนใน publication ต่างจาก CIHP +121 [Original paper]({PAPER})

Author card แยก Human_ids=person instances และ Instance_ids=attribute instances; ส่วน Category_ids เป็น semantic attributes **ต้องตรวจ masks/code ก่อนถือว่าเท่ากับ native CIHP part-instance encoding** [Author dataset documentation]({CARD})

เอกสารมี version/count discrepancy: paper กล่าวถึง 19 foreground semantic classes; author card ระบุ 20 แต่ list เรียงถึง 21 พร้อม Bag/Others จึงเก็บเป็น **UNRESOLVED_RELEASE_TAXONOMY_VERSION** ไม่ใช้ค่า documentation เป็น local class inventory ไม่ผูก documentation ordinal เป็น PNG class ID ที่ตรวจแล้ว

[Class-by-class draft matrix](../taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv) แยก published incompatibilities กับ NOT_VERIFIED local equivalence ไม่มี EXACT/VERIFIED_EQUIVALENT ที่อ้างว่า CCIHP pixel-level ผ่านแล้ว ไม่ freeze mapping

## 4. GT recovery: native และ custom แยกกัน

Native CIHP benchmark: **BLOCKED** เพราะ Human GT ไม่มี และยังไม่มี independent original human-ID equivalence evidence การต่อ semantic CIHP กับ human maps ที่ถูกเปลี่ยนใน CCIHPจะเป็น mixed-source GT จนกว่าจะพิสูจน์ fidelity ห้ามเรียก official native GT

Custom semantic/common-taxonomy track: **CONDITIONAL** — existing CIHP conversion มี semantic parts ที่ใช้เสนอ track แยกได้หลัง quality/permission/common-domain review แต่ไม่ทำให้ person matching/person-macro/APp/coverage-aware instance tracks พร้อม

Custom CCIHP-person track: **NOT_TESTED/BLOCKED** เพราะ CCIHP data ยังไม่มีจริง ถ้าได้ภายหลังต้องทำ same-RGB/coordinate/semantic/person tests ใหม่; document-only taxonomy evidence ไม่แทน masks

## 5. Integrity, quality และ license

Reuse prior full audit: all 38,280 image/JSON pairs, 33,280 labeled images, 768,446 valid converted bitmaps; test JSON ว่าง 5,000 ตาม hidden GT design อย่างไรก็ดี full strict-RGB/physical ownership/near-duplicate quality ยังไม่ผ่าน Full Quality Audit Native demos ไม่เป็น representative quality sampling

Known reuse เดิม: **39 train–val JPEG-byte groups / 39 val IDs**, 83 cross-split groups; no exclusions/split edits ไม่อ่าน pixels ซ้ำทั้งชุดหรืออ้างว่า exact bytes audit ครอบ near duplicates

Reuse Decision 5A scope/license matrix; ไม่ audit parser licenses ใหม่ Author CCIHP card ประกาศ annotation CC-BY-NC-4.0 และ evaluation-code MIT ซึ่งเข้ากับ noncommercial academic scope ตามเงื่อนไข แต่ **ไม่มี local CCIHP LICENSE ให้ตรวจ** และสิทธิ์ CCIHP annotations ไม่โอน original CIHP RGB rights ส่วน TAR provider MIT ไม่ใช่ original RGB/GT owner grant [Prior license assessment](LICENSE_ELIGIBILITY_REASSESSMENT.md), [research scope](../RESEARCH_SCOPE.md)

## 6. ข้อสรุปและ stop gate

เลือก **C — NATIVE_CIHP_REQUIRED สำหรับข้อมูลที่มีปัจจุบัน** ขอ verified original CIHP Human_ids/Category_ids/Instance_ids/splits supplement หรือ native distribution ภายหลัง approval; ไม่จำเป็นต้อง download DatasetNinja TAR เดิมอีก

ถ้าต้องการใช้ CCIHP ใน custom track ต้องโอน actual CCIHP annotations มาแล้ว audit ต่างหาก ชื่อที่เรียก TAR ไม่เพิ่มข้อมูล person GT การโอน CCIHPอย่างเดียวไม่ทำให้ native equivalence อัตโนมัติ [Recovery decision](CIHP_GROUND_TRUTH_RECOVERY_DECISION.md)

Full Quality Audit / ~200 stratified TRAIN human review ยังรอ native-human input และ approval คง CIHP candidate-primary/MHP-v2 provisional-secondary, taxonomy DRAFT, benchmark NOT_STARTED ไม่มี PPSS/CCTV/models/training/color-pattern-size evaluation
''')

images = {x['image_id']: x['diagnostic_image'] for x in bounded['actual_cases'] if x.get('diagnostic_image')}
publish('reports/CCIHP_PERSON_INSTANCE_VERIFICATION.md', f'''# Stage 0E — Person Instance Verification

**Human_ids validation: BLOCKED / NOT_TESTED** Actual archive=`datasets/cihp-DatasetNinja.tar` เป็น CIHP conversion ไม่ใช่ CCIHP release ไม่มี source Human_ids, person-to-part metadata หรือ original human reference masks

| Requirement | ผล actual source | สิ่งที่ยังยืนยันไม่ได้ |
|---|---|---|
| หนึ่ง Human ID = หนึ่ง physical person | NOT_TESTED — Human_ids absent | Ownership, number/order/person support |
| Visible-person completeness | NOT_TESTED | Unannotated background people vs original policy |
| Semantic/human spatial relation | Semantic demo dimensions PASS; human relation unavailable | Exact person assignment / mixed-source differences |
| Multi-person ownership | BLOCKED | Part object IDs เป็น object IDs ไม่ใช่ person IDs |
| Ignore/overlap/occlusion conventions | Converted background implicit; native-human policy unresolved | ไม่ตีความ 255 เป็น ignore หรือ overlap เป็น error โดยไม่มี source definition |
| GT matching/person-macro | BLOCKED | Foreground union/connected components/YOLO แทน native GT ไม่ได้ |
| Within-image identity consistency | NOT_TESTED | Person namespaces/counts ไม่ปรากฏใน JSON |

Whole-archive schema audit เดิมพบ object/image tags ว่างและไม่มี ownership fields; fresh payload reads ยืนยันตัวอย่างเดียวกันอีกครั้ง ไม่มี person masks ถูกสร้างด้วย heuristics Person denominator จึง **null/unknown** ไม่ใช้ 768,446 part objects เป็นจำนวนคน

## ภาพที่ตรวจจริง: semantic alignment เท่านั้น

ภาพต่อไปนี้ใช้ RGB เดิม, pinned official PGN semantic demo และ DatasetNinja reconstruction; categorical arrays ไม่ resize สำหรับ metric parity ภาพแสดงผล resize หลังทำ overlay เท่านั้น ไม่เปลี่ยน GT ไม่มี CCIHP/human-mask panel สมมติ

### 0002190 — คนใกล้กันในภาพเดียว

![CIHP semantic comparison](../{images['0002190']})

Observation: มองเห็นคนสองคนใกล้กันและ semantic regions ทั้งสองฝั่งตรงกัน ตัวเลข parity คือ 0 differing pixels

Interpretation: semantic correctness ไม่แสดงว่า hair/upperclothes pixels แต่ละส่วนผูกกับคนใด ห้ามใช้ shared class color เป็น human ID หรือเชื่อม ownership จาก connectivity

### 0005008 — กลุ่มคนหลายคนและหลาย part objects

![CIHP crowded semantic comparison](../{images['0005008']})

Observation: คนหลายคนเรียงใกล้กันและมีขอบเขตเสื้อ/ส่วนร่างกายหลายส่วน JSON มี **53 part objects**; official/DatasetNinja semantic regions ตรงกันทุก pixel

Interpretation: part-object count ไม่ใช่ person count ภาพนี้ไม่พิสูจน์ visible-person completeness หรือ native ownership จึงไม่สร้าง person IDs จากการมองภาพ/สี overlay

### 0012008 — คนอยู่ใกล้กันและมีวัตถุร่วมในฉาก

![CIHP nearby people semantic comparison](../{images['0012008']})

Observation: มีคน foreground หลายคนและร่มในภาพ ส่วนร่างกาย/เสื้อผ้าหลายบริเวณอยู่ชิดกัน; semantic parity ผ่านที่ original grid

Interpretation: shared semantic labels ไม่พอแยก ownership และ native human-mask support ของ accessories ต้องตรวจ source จริง ไม่เดาจาก parsing foreground union

## ขอบเขตหลักฐาน

Inspect ภาพทั้งสามจริงและทำ numeric parity รวม 5 train demos ไม่มี human-instance visual verification หรือ error-prevalence estimate CCIHP paper กล่าวถึง modified human masks เป็น warning เชิง compatibility ไม่ใช่ผล local masks ที่ตรวจแล้ว Source absent ห้ามแปลเป็น corruption ของ CCIHP

[Main audit](CCIHP_CIHP_COMPATIBILITY_AUDIT.md), [machine evidence](../provenance/CCIHP_ARCHIVE_AUDIT.json), [decision](CIHP_GROUND_TRUTH_RECOVERY_DECISION.md)
''')

publish('reports/CIHP_GROUND_TRUTH_RECOVERY_DECISION.md', '''# CIHP Ground Truth Recovery Decision — Stage 0E

**Decision C — NATIVE_CIHP_REQUIRED (current assets). Native benchmark readiness: BLOCKED.**

ผู้ใช้ยืนยันไฟล์ `datasets/cihp-DatasetNinja.tar` เป็นเป้าหมาย การอ่าน README/LICENSE/meta/JSON และ native demo parity พบว่าเป็น CIHP semantic-part conversion **ไม่ใช่ CCIHP release** ไม่มี Human_ids/grouping จึงไม่กู้ native per-human parsing/GT matching/person denominator จากไฟล์นี้อย่าง defensible ได้

| Output task | Current feasibility | ขอบเขต |
|---|---|---|
| Global semantic/body/clothing regions | CONDITIONAL | Converted parts verified structurally; native demo parity 5 only; full quality/license/common projection pending |
| Native GT person IDs | BLOCKED | Original Human_ids missing; object IDs ไม่ใช่ person IDs |
| Per-person native parsing | BLOCKED | No lossless person ownership; original mapping source necessary |
| Oracle geometry / GT person matching | BLOCKED | Heuristic bbox/connected components ไม่แทน physical ownership |
| Person-macro/coverage-aware parsing | BLOCKED | Native person populations/support undefined |
| Native CIHP APp/PCP targets | BLOCKED | Semantic demo referencesไม่เพียงพอ; original instance/part metadata required |
| Custom CCIHP common track | NOT_TESTED | Actual CCIHP absent; future independent custom source audit required |

## เหตุผลที่ไม่เลือก A/B/D

A ไม่มี original person-equivalence evidence และ paper ยืนยัน CCIHP annotations เปลี่ยนจาก CIHP B อาจเหมาะเมื่อมี actual CCIHP ให้ตรวจ custom-person information แต่ตอนนี้ไม่มี source Human_ids เลย D จะเหมาะกับการตัดสิน unseen CCIHP archive; อย่างไรก็ดีสำหรับ **actual available TAR** มีหลักฐานพอว่าข้อมูล ownership หาย จึงเลือก C ไม่อ้างว่า CCIHP ทุก release ไม่มีประโยชน์

## Next bounded execution หลังอนุมัติ

1. Obtain original native CIHP GT supplement หรือ distribution ที่ verified source มี Human_ids/Category_ids/Instance_ids และ full original lists ก่อน ไม่ต้องโหลด DatasetNinja conversion ซ้ำ หากมี copy บน server ให้ตรวจ copy นั้นก่อน download
2. Small same-frame source fidelity gate: image IDs/RGB identity/grids, native class IDs/void, every part's human association, semantic/person count consistency เทียบ original reference หลาย-person cases ไม่ flatten overlaps/guess ownership
3. เมื่อ small gate ผ่านจึงเสนอ Full Quality Audit: strict decode ทั้งชุด, exact/near reuse, native distributions และ ~200 deterministic stratified TRAIN human-review sample ตาม existing V2 plan ไม่เลือก from validation หรือตั้ง primary จาก file-integrity PASS อย่างเดียว

**อีก CIHP download จำเป็นหรือไม่:** native-person GT เพิ่มจำเป็น แต่ full RGB distribution download อาจไม่จำเป็นถ้าได้ verified GT-only supplement/local native copy หากไม่มี supplement ให้ขออนุมัติ official native distribution แยกก่อน; **ยังไม่อนุมัติหรือเริ่ม download**

ถ้าได้ CCIHP จริง สามารถ audit custom cohort ต่างหากได้ แต่การประกอบ native CIHP semantic × modified CCIHP Human_ids ต้องผ่าน fidelity/denominator tests และห้ามเรียก official CIHP หาก person/region target เปลี่ยน การไม่มี file ในรอบนี้ไม่ให้ข้อสรุปเชิง pixel ของ CCIHP

Reuse Decision 5A license findings แยก original CIHP image rights, CCIHP annotation CC-BY-NC declaration, DatasetNinja provider terms และ model weights ไม่ใช้ license ของ source หนึ่งแทนอีก source

[Compatibility audit](CCIHP_CIHP_COMPATIBILITY_AUDIT.md), [Human evidence](CCIHP_PERSON_INSTANCE_VERIFICATION.md), [draft matrix](../taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv), [~200 review plan](../manifests/CIHP_QUALITY_REVIEW_PLAN_V2.json)

**STOP — WAIT FOR USER APPROVAL.** No source edits/download/model inference, no PPSS/CCTV/attributes, no Stage 1 or benchmark
''')
amendments = {
    'reports/CIHP_QUALITY_AUDIT.md': '''\n## Stage 0E — Actual archive identity and person-GT recovery

ผู้ใช้ระบุ TAR นี้ว่า CCIHP แต่ actual README/LICENSE/meta/annotations ยืนยัน **CIHP DatasetNinja conversion, not CCIHP** ไม่มี CCIHP_icip.zip/native Human_ids source บน workspace ไม่ใช้ชื่อที่เรียกเป็นหลักฐาน release identity

Fresh bounded recheck 5 official TRAIN demos: RGB/semantic pixels ตรงทั้งหมด, 0 differing pixels; GT diagnostics 3 images inspect แล้ว ไม่มี person GT reconstructed Publication CCIHP ระบุ modified semantic/human targets จึงไม่ silently substitute CCIHP Human_ids เป็น native CIHP

**Decision C — native GT supplement/distribution required for current assets**; full download อาจเลี่ยงได้ถ้ามี verified original GT-only supplement ไม่เริ่ม acquisition/Full Quality Audit/benchmark Native ~200-image human reviewยังรอ input

[Stage 0E audit](CCIHP_CIHP_COMPATIBILITY_AUDIT.md), [person verification](CCIHP_PERSON_INSTANCE_VERIFICATION.md), [GT decision](CIHP_GROUND_TRUTH_RECOVERY_DECISION.md), [evidence](../provenance/CCIHP_ARCHIVE_AUDIT.json)
''',
    'reports/PRIMARY_DATASET_DECISION.md': '''\n## Stage 0E compatibility amendment

Actual `cihp-DatasetNinja.tar` เป็น CIHP conversion ไม่ใช่ CCIHP annotations ไม่มี human ownership และ native CCIHP source absent พบ native-semantic demo parity 5/5 แต่ไม่แก้ person-instance contract **Decision C: original native CIHP GT supplement/distribution needed** ไม่ promote CIHP และไม่เปลี่ยน dataset-role draft

CCIHP publication เปลี่ยน semantic categories/human masks การใช้แทนต้องตรวจ fidelity หรือประกาศ custom track ชัดเจน ดู [recovery decision](CIHP_GROUND_TRUTH_RECOVERY_DECISION.md) และ [class-by-class matrix](../taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv) Common taxonomy ยังไม่ freeze ไม่มี color/attribute study
''',
    'reports/STAGE0_NEXT_ACTIONS.md': '''\n## Stage 0E — GT-source decision ที่ตรวจแล้ว

ไฟล์ที่ผู้ใช้เรียก CCIHP คือ `cihp-DatasetNinja.tar`; payload ยืนยัน **CIHP DatasetNinja**, no Human_ids source. ไม่มี CCIHP_icip.zip/extracted copy จึงไม่รายงาน CRC/mask/GT equivalence ว่าผ่าน Fresh semantic-only native demo comparisons 5 ภาพ mismatch 0 และ inspected GT overlays 3 ภาพ; source/person denominator missing

**C — Native CIHP required สำหรับ assets ตอนนี้:** ขอ verified original native GT-only supplement/local copy ก่อน; หากต้อง official download ให้ขอ approval แยก ไม่ download conversion ซ้ำ ไม่ต้องรีบโหลด CCIHP เพื่อหวังว่าเท่ากับ native เพราะ publication ระบุแก้ human/semantic annotations

หลัง input gate ผ่าน ค่อยเสนอ Full Quality Audit/200 TRAIN review ด้วย existing V2 plan FASHN smoke/download approval ยัง pending แยกต่างหาก รอบ Stage 0E ไม่อนุมัติ weights, dependencies, benchmarking หรือ CCTV

[Stage 0E findings](CCIHP_CIHP_COMPATIBILITY_AUDIT.md), [GT recovery decision](CIHP_GROUND_TRUTH_RECOVERY_DECISION.md), [machine evidence](../provenance/CCIHP_ARCHIVE_AUDIT.json)
'''}
for name, amendment in amendments.items():
    publish(name, (ROOT / name).read_text() + amendment)
publish('README.md', (ROOT / 'README.md').read_text() + '''\n## Stage 0E — CCIHP / native CIHP compatibility

[Actual-source audit](reports/CCIHP_CIHP_COMPATIBILITY_AUDIT.md), [person-GT verification](reports/CCIHP_PERSON_INSTANCE_VERIFICATION.md), [recovery decision](reports/CIHP_GROUND_TRUTH_RECOVERY_DECISION.md), [matrix](taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv), [machine evidence](provenance/CCIHP_ARCHIVE_AUDIT.json).

The user-identified TAR is **CIHP DatasetNinja conversion**, not a verified CCIHP release. No local CCIHP archive/Human_ids exists. Five pinned native semantic demo checks pass, but person ownership remains unavailable. **Decision C: verified native CIHP GT supplement/distribution required for current assets.** Primary roles/common taxonomy remain draft; acquire nothing without approval. No model/benchmark/attribute/CCTV/PPSS execution.
''')
state = json.loads((ROOT / 'STUDY_STATE.json').read_text())
state['last_updated_utc'] = NOW
state['stage0e_ccihp_cihp'] = {'run_id': active['run_id'], 'status': 'BLOCKED', 'actual_archive_identity': 'CIHP_DATASETNINJA_NOT_CCIHP',
                              'ccihp_source_present': False, 'human_gt_ready': False, 'native_demo_semantic_parity': 'PASS_5_CASES',
                              'decision': 'C_NATIVE_CIHP_REQUIRED_CURRENT_ASSETS', 'primary_promoted': False,
                              'download_started': False, 'benchmark_started': False, 'report': 'reports/CCIHP_CIHP_COMPATIBILITY_AUDIT.md',
                              'evidence': 'provenance/CCIHP_ARCHIVE_AUDIT.json', 'review_gate': 'WAIT_FOR_USER_APPROVAL'}
save('STUDY_STATE.json', state)
save('provenance/CCIHP_STAGE0E_DOCUMENT_REVISIONS.json', {'run_id': active['run_id'], 'revisions': revisions, 'new_artifacts': created})
print(json.dumps({'decision': 'C', 'human_GT': 'BLOCKED', 'native_semantic_parity': '5/5',
                  'class_matrix_rows': len(rows), 'archived_documents': len(revisions), 'new_reports': 3}, ensure_ascii=False))
