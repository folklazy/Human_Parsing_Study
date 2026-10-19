"""Publish Stage 0E continuation after actual CCIHP becomes locally available."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import difflib
import hashlib
import io
import json

ROOT=Path(__file__).resolve().parents[1]
active=json.loads((ROOT/'provenance/CCIHP_STAGE0E_CURRENT_RUN_V2.json').read_text())
RUN=ROOT/active['run_path']
ARCHIVE=ROOT/'reports/archive'/active['run_id']
NOW=datetime.now(timezone.utc).isoformat()
revisions=[]
created=[]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def publish(name,text):
    path=ROOT/name
    if path.exists():
        original_bytes=path.read_bytes();old=original_bytes.decode('utf-8');backup=ARCHIVE/name;backup.parent.mkdir(parents=True,exist_ok=True)
        with backup.open('xb') as f:f.write(original_bytes)
        backup.with_name(backup.name+'.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),text.splitlines(True),fromfile=name+' BEFORE',tofile=name+' AFTER')))
        revisions.append({'original_relative':name,'archived_relative':str(backup.relative_to(ROOT)),'sha256_before':sha(path),
                          'sha256_after':hashlib.sha256(text.encode()).hexdigest(),'timestamp_utc':NOW,
                          'reason':'Actual CCIHP added: supersede missing-input gate with bounded compatibility evidence'})
    else:created.append(name)
    tmp=path.with_name(path.name+'.tmp-'+active['run_id'])
    with tmp.open('x') as f:f.write(text)
    tmp.replace(path)


def save(name,value):publish(name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')


zip_e=json.loads((RUN/'ZIP_INTEGRITY.json').read_text())
cross=json.loads((RUN/'BOUNDED_CROSS_DATASET_COMPARISON.json').read_text())
fidelity=json.loads((RUN/'CCIHP_GT_FIDELITY.json').read_text())
split=json.loads((RUN/'SPLIT_COMPONENT_VALIDATION.json').read_text())
old_matrix=list(csv.DictReader((ROOT/'taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv').open()))
classstats=cross['per_class_same_numeric_ID_diagnostics']
matrix=[]
for old in old_matrix:
    native_id=old['cihp_native_id'];position=old['ccihp_author_documented_position'];stat_=classstats.get(native_id,{})
    concept=old['ccihp_documented_concept']
    if native_id=='7':status='AMBIGUOUS';reason='Local README coat rule and sampled upperclothes/coat relabeling prevent native target equivalence'
    else:status=old['compatibility_status'];reason=old['reason']
    matrix.append({'cihp_native_id':native_id,'cihp_native_name':old['cihp_native_name'],'ccihp_declared_id':position,
                   'ccihp_declared_concept':concept,'compatibility_status':status,
                   'CCIHP_ID_observed_in_30_samples':str(position).isdigit() and int(position) in cross['observed_Category_ids'],
                   'CCIHP_pixels_same_ID_in_sample':stat_.get('pixels_CCIHP','NO_DISTINCT_NATIVE_CLASS'),
                   'CIHP_pixels_in_sample':stat_.get('pixels_CIHP','NO_DISTINCT_NATIVE_CLASS'),
                   'same_ID_class_mask_difference_pixels':stat_.get('differing_label_pixels','NOT_APPLICABLE'),
                   'pixel_comparison_scope':'Same numeric ID diagnostic; not a harmonized metric or semantic equivalence proof',
                   'reason':reason,'source':'Included CCIHP README + pinned native CIHP taxonomy + 30 paired cases',
                   'mapping_frozen':False})
matrix.append({'cihp_native_id':'UNSUPPORTED_UNDOCUMENTED','cihp_native_name':'No verified counterpart','ccihp_declared_id':22,
               'ccihp_declared_concept':'UNDOCUMENTED_SOURCE_VALUE','compatibility_status':'NOT_VERIFIED',
               'CCIHP_ID_observed_in_30_samples':True,'CCIHP_pixels_same_ID_in_sample':2,'CIHP_pixels_in_sample':'NOT_APPLICABLE',
               'same_ID_class_mask_difference_pixels':'NOT_APPLICABLE','pixel_comparison_scope':'Training/0033810; keep exact original values',
               'reason':'Two pixels at (301,162),(302,162); README lists only0..21; ignore/void/remapping not authorized',
               'source':'Actual Category_ids PNG with valid ZIP/PNG CRC','mapping_frozen':False})
stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(matrix[0]));writer.writeheader();writer.writerows(matrix)
publish('taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv',stream.getvalue())

associations=cross['association_counts'];total_parts=sum(associations.values())
unknown=[{'split':x['split'],'image_id':x['image_id'],'labels':x['undocumented_semantic_ids'],
          'pixels':x['undocumented_semantic_pixels'],'coordinates_xy':x['undocumented_semantic_coordinates_xy']}
         for x in cross['cases'] if x['undocumented_semantic_ids']]
facts={'schema_version':'2.0','run_id':active['run_id'],'timestamp_utc':NOW,'requested_ccihp_archive_present':True,
       'archive_workspace_relative':'datasets/CCIHP_icip.zip','archive_bytes':zip_e['archive_bytes'],'archive_sha256':zip_e['archive_sha256'],
       'release_identity':'CCIHP_icip; included README/license/citation consistent with author CCIHP documentation',
       'publisher_binary_checksum':'NOT_AVAILABLE','download_receipt_source':'USER_TRANSFERRED_EXACT_UPSTREAM_DOWNLOAD_NOT_INDEPENDENTLY_VERIFIED',
       'zip_member_count':zip_e['members'],'zip_regular_members':zip_e['regular_files'],'all_member_crc':'PASS','safe_archive_paths':'PASS',
       'member_inventory':zip_e['member_inventory'],'member_inventory_sha256':zip_e['member_inventory_sha256'],
       'CCIHP_train_annotation_sets':28280,'CCIHP_validation_annotation_sets':5000,'CCIHP_test_annotation_sets':'NOT_SUPPLIED_EXPECTED',
       'CCIHP_RGB_images_in_archive':0,'missing_required_train_val_components':0,
       'available_layers':['Category_ids','Human_ids','Instance_ids','Color_ids','Pattern_ids','Size_ids'],
       'validation_extra_layer':'Charac_instance_ids (structural identification only)',
       'CIHP_datasetninja_archive':'datasets/cihp-DatasetNinja.tar','rehashed_datasetninja_whole_archive':False,
       'train_validation_membership_vs_datasetninja':'EXACT_BOTH_SPLITS',
       'semantic_readability_grid_tests':{'images':30,'pngs':90,'status':'PASS'},
       'sample_split_counts':{'Training':25,'Validation':5},'validation_integrity_only_not_model_tuning':True,
       'native_CCIHP_person_planes_in_sample':96,'all_source_grid_roundtrip':'PASS_30_CASES',
       'CCIHP_full_person_count':'NOT_COMPUTED_IN_BOUNDED_AUDIT','declared_foreground_classes':21,'declared_background':0,
       'observed_category_values_sample':cross['observed_Category_ids'],'undocumented_category_values':unknown,
       'human_semantic_coverage_gaps_pixels':12,'category_foreground_without_human_pixels':0,
       'attribute_instances_without_human_pixels':0,'sample_attribute_instances':840,'single_human_and_category_attribute_instances':840,
       'CIHP_parts_checked':total_parts,'CIHP_part_to_CCIHP_human_association':associations,
       'raw_same_numeric_ID_semantic_difference_pixels':sum(x['raw_same_ID_semantic_difference_pixels'] for x in cross['cases']),
       'foreground_difference_pixels':sum(x['foreground_difference_pixels'] for x in cross['cases']),
       'numeric_difference_is_not_quality_score_or_harmonized_metric':True,
       'independent_CCIHP_RGB_identity':'NOT_TESTED_NO_CCIHP_RGB_COPY; use documented shared CIHP RGB',
       'native_CIHP_semantic_reference_parity':'PASS_5_OFFICIAL_TRAIN_DEMOS_FOR_DATASETNINJA',
       'native_CIHP_human_reference_parity':'NOT_TESTED_REFERENCE_UNAVAILABLE',
       'ignore_and_amodal_overlap_conventions':'UNRESOLVED; do not assume semantic holes or unknown22 are ignore',
       'physical_person_review':{'images':3,'dominant_foreground_alignment':'OBSERVED','complete_visible_person_coverage':'NOT_VERIFIED'},
       'annotation_license':'CC-BY-NC-4.0_VERIFIED_INCLUDED_LICENSE_AND_README','evaluation_code_license':'MIT_VERIFIED_HEADERS',
       'scope_decision':'5A_REUSED','original_CIHP_RGB_rights':'UNRESOLVED_PREVIOUS_ASSESSMENT','DatasetNinja_terms':'PROVIDER_MIT_NOT_ORIGINAL_RIGHTS_GRANT',
       'decision':'B','decision_name':'PARTIALLY_COMPATIBLE','native_CIHP_GT_ready':False,
       'custom_CCIHP_person_GT_feasibility':'CONDITIONAL_FULL_QUALITY_TAXONOMY_DATASET_RIGHTS_REVIEW',
       'official_CIHP_download':'NOT_REQUIRED_TO_CONTINUE_CUSTOM_AUDIT; VERIFIED_NATIVE_GT_REQUIRED_FOR_NATIVE_CIHP_TRACK',
       'taxonomy_frozen':False,'primary_dataset_promoted':False,'new_inference':False,'originals_modified':False,
       'dataset_or_checkpoint_download':False,'full_benchmark':False,'ppss_activity':False,'cctv_activity':False,'attributes_evaluated':False,
       'prior_stage0e_missing_archive_assessment':'Historical C applied before ZIP arrived; preserved in versioned archive',
       'zip_evidence':str((RUN/'ZIP_INTEGRITY.json').relative_to(ROOT)),
       'cross_dataset_evidence':str((RUN/'BOUNDED_CROSS_DATASET_COMPARISON.json').relative_to(ROOT)),
       'fidelity_evidence':str((RUN/'CCIHP_GT_FIDELITY.json').relative_to(ROOT)),
       'matrix':'taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv','report':'reports/CCIHP_CIHP_COMPATIBILITY_AUDIT.md'}
save('provenance/CCIHP_ARCHIVE_AUDIT_V2.json',facts)
save('provenance/CCIHP_ARCHIVE_AUDIT.json',facts)

case_rows='\n'.join(f"| {x['image_id']} | {len(x['person_ids'])} | {x['raw_same_ID_semantic_difference_pixels']:,} | {x['foreground_difference_pixels']:,} |" for x in cross['cases'] if x['native_demo_reference'])
publish('reports/CCIHP_CIHP_COMPATIBILITY_AUDIT.md',f'''# Stage 0E — CCIHP / CIHP GT Compatibility Audit

**Current bounded execution: PASS_WITH_WARNINGS. Decision B — PARTIALLY_COMPATIBLE. Native CIHP equivalence: BLOCKED. Full Quality Audit: NOT_STARTED.**

CCIHP ZIP เพิ่มมาแล้วหลังการตรวจรอบก่อน รายงานก่อนที่ระบุ source missing/Decision C ถูกเก็บพร้อม hashes ใน archive ไม่เปลี่ยนข้อเท็จจริงของรอบก่อน และไม่เริ่ม Stage 0 ใหม่

## 1. Actual archives / provenance

| รายการ | CCIHP | CIHP DatasetNinja |
|---|---|---|
| Workspace-relative source | `datasets/CCIHP_icip.zip` | `datasets/cihp-DatasetNinja.tar` |
| Size | 842,868,844 bytes | 2,015,375,360 bytes |
| Actual role | Annotation-only CCIHP_icip release | CIHP RGB + converted semantic part bitmaps |
| Human GT | Human_ids present | Original human ownership omitted |
| Integrity | All-member ZIP CRC + SHA inventory PASS | Reuse complete preflight; no whole TAR rehash |

CCIHP SHA256: `{zip_e['archive_sha256']}`. ZIP มี **209,707 members / 209,688 regular files**, safe paths/no duplicates/no symlinks, 877,848,629 uncompressed bytes ทุก payload อ่าน/CRC/SHA256ครบ ไม่มี full extraction

Included README/LICENSE/evaluation-source headers ตรงกับ CCIHP ICIP 2021 documentation แต่ไม่มี publisher checksum/download receipt อิสระยืนยัน binary identity Local SHA พิสูจน์ไฟล์ที่ตรวจ ไม่รับรองต้นทางเกินหลักฐาน

## 2. Completeness / splits / geometry

Train **28,280 annotation sets**, Validation **5,000**, รวม **33,280** ทั้ง Category_ids/Human_ids/Instance_ids/Color_ids/Pattern_ids/Size_ids จับคู่ IDs/split lists ครบไม่มี missing/orphan Train/Val IDsไม่ซ้ำกัน และตรงกับ DatasetNinja **ทั้งสอง split ทุก ID** ไม่ใช้ filenames เป็น RGB-identity proof

Validation มี Charac_instance_ids อีก 5,000 ไฟล์และ evaluation lookup tables; inspect เฉพาะ structure/CRC ไม่รัน color/pattern/size evaluation ZIP ไม่มี RGB และไม่มี test annotations; ไม่ถือ hidden test GT เป็น corruption

Strict PNG CRC/full-load/grid checks **30 images × 3 maps = 90 PNGs**: 25 TRAIN (20 SHA-ranked + 5 previous native demos) และ 5 VAL เพื่อ integrity/compatibility เท่านั้น ไม่ใช้ปรับ model/taxonomy thresholds หรือเลือกจาก runtime ผลนี้ไม่ใช่ full semantic audit ทั้ง 33,280 ชุด

RGB ใช้จาก CIHP TAR ตาม CCIHP documentation ที่ประกาศ shared images; 30 grids ตรงและดู alignment 3 ภาพ มี official native CIHP RGB/semantic references 5 TRAIN demos ที่ยืนยัน DatasetNinja byte/pixel parity แต่ CCIHP ไม่มี RGB copy ให้เทียบ independent bytes จึงไม่อ้าง CCIHP-RGB byte equality ที่ไม่ได้ตรวจ

## 3. Human_ids / Instance_ids

Human_ids samples เป็น uint8 image-local IDs, background0; Category_ids uint8 และ Instance_ids uint16 ไม่สับสน part-instance IDs กับ person IDs ไม่ downcast หรือทำ connected-component person reconstruction

30 ภาพมี **96 source person IDs**, **840 attribute instances** ทุก sampled attribute instance มีหนึ่ง positive human ID และหนึ่ง positive semantic ID แยก native CCIHP per-person planes และ recompose source maps ได้ตรงทุก pixel **30/30 PASS** เก็บ human support ต่างหากจาก semantic foreground จึงไม่ทิ้ง human pixels ที่ไม่มี category

Cross-map coverage: category foreground without human=0; instance without human=0; human without category=**12 pixels** ต้องตรวจ semantics/annotation intent ไม่เรียก overlap/holes ว่า error โดยอัตโนมัติ Original Human_ids เป็น single-valued visible-grid representation; ไม่มีหลักฐานเพียงพอเรื่อง amodal/occluded completion หรือ full visible-person completeness

[Person verification with full-frame images](CCIHP_PERSON_INSTANCE_VERIFICATION.md), [lossless fidelity](../{str((RUN/'CCIHP_GT_FIDELITY.json').relative_to(ROOT))}) ไม่ประมาณ physical-ownership error prevalence จาก 3 inspected examples

## 4. Native semantic equivalence ไม่ผ่าน

Included README กำหนด 1–21 foreground concepts (รวม Face Mask6, Bag20, Others21), background0 ส่วน original CIHP มี Dress6 และไม่มี standalone Bag/Others/FaceMask Same numeric ID ไม่ใช่ same semantic target Dressถูกแยก UpperClothes/Skirt, glasses/scarf/hair เปลี่ยน scope; paper ยืนยัน human masks ถูกปรับด้วย [Original publication §2](https://arxiv.org/html/2201.09594v1#S2)

Same-frame raw ID differences ที่ native demos (เป็น **diagnostic counts**, ไม่ใช่ harmonized metric/quality score):

| TRAIN demo | CCIHP person IDs | Semantic raw-ID differing pixels | FG/BG differing pixels |
|---|---|---|---|
{case_rows}

รวม 30 samples raw semantic difference **304,537 pixels**, FG/BG difference **35,492 pixels** การเปลี่ยน semantic definition และ mask boundariesปนกัน จึงไม่ตีความเป็น corruption/accuracy drop หรือ causal effect รายการที่ไม่เปลี่ยนชื่อยังไม่พิสูจน์ exact benchmark-equivalent target

[Class-by-class matrix](../taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv) มี observed support/diagnostic differences และ incompatible/ambiguous/NOT_VERIFIED distinctions Common mapping ยัง DRAFT ไม่มี universal coarse remapping ที่ silently hide difficult GT

## 5. Can DatasetNinja parts inherit CCIHP person IDs?

ตรวจ **741 CIHP part objects** ใน 30 frames กับ CCIHP Human_ids:

| Association outcome | Objects |
|---|---|
| One human ID covers full object support | 694 |
| Object covers multiple human IDs | 21 |
| One human ID plus unassigned/background pixels | 26 |

จึงไม่สามารถ claim every native CIHP object มี unambiguous CCIHP owner Splitting objects by CCIHP masks หรือเลือก majority owner จะเป็น **derived mixed-source GT policy** ไม่ใช่ original native CIHP ที่พิสูจน์แล้ว No heuristics applied Native human reference unavailable จึงยังไม่ทราบว่า label conflicts เกิดจาก annotation correction/boundary changes/ownership mistakes อย่างใด

## 6. Annotation warnings / source code caveats

พบ TRAIN `0033810` มี Category_ids **22 จำนวน 2 pixels** ที่ original xy `(301,162),(302,162)` นอก README0–21 definition Source ZIP/PNG CRC valid ค่าเดิมคงไว้; classification=`UNRESOLVED_UNDOCUMENTED_LABEL` ไม่ assign เป็น background/void ไม่สรุปว่าทั้ง dataset corrupt [Exact evidence](../{str((RUN/'UNEXPECTED_CATEGORY_SCREEN.json').relative_to(ROOT))})

README/paper/release versionแตกต่าง: paperเดิม19 foreground; local README21 foreground และพบ22ที่ยังไม่อธิบาย Evaluation generator default `class_num=21` อาจไม่รวม Others21; metric script maps labels>=num_classes เป็น background จึง **ห้ามนำ defaults มา freeze study scoring** โดยไม่ตรวจ ไม่ execute/patch upstream codeหรือ attribute metrics

Known CIHP split leakage reused: **39 train–val JPEG-byte groups / 39 validation IDs**, 83 all-cross-split groups Membership ของ CCIHPตรงสอง split จึงต้อง disclose risk เดิม ไม่ claim split independence Near-duplicate/decoded full checks และ CCIHP duplicate-annotation fidelityยัง NOT_TESTED ไม่เปลี่ยน lists/exclude samples

## 7. License / research scope

Reuse user-confirmed **Decision 5A — independent noncommercial academic research/evaluation** Local CCIHP annotation LICENSEเป็น **CC-BY-NC-4.0**, READMEและevaluation .py headersแยก code **MIT** เข้ากับ research scope ภายใต้ attribution/notices แต่ไม่ได้โอนสิทธิ์ original CIHP RGB/GT ซึ่งยัง unresolved ตาม reviewเดิม DatasetNinja provider MIT ก็ไม่ใช่ RGB-owner grant ไม่ audit parser licensesใหม่ ไม่ใช้ CCTV

## 8. Decision / next gate

**B — PARTIALLY_COMPATIBLE:** CCIHP own human+semantic+attribute-instance GT กู้เป็น lossless per-person recordsได้ใน samplesและมี source filesครบ แต่ modified targets/ambiguous cross-source linksทำให้ **A — native CIHP compatible ยังไม่ผ่าน**

Native CIHP benchmark routeยังต้อง original verified GT supplement/distribution; **ไม่จำเป็นต้อง downloadเพิ่มเพื่อไปต่อ bounded/full quality audit ของ custom CCIHP-person track หากผู้ใช้เลือกและอนุมัติ trackนี้** ทั้งสอง routeต้องแยกชื่อ dataset/targets/denominatorsและไม่เรียก custom score official CIHP

ก่อน freeze: ทำ Full Quality Audit ตาม trackที่เลือก, resolve unknown22/coverage/visible ownership/ignore conventions และ review ~200 deterministic stratified TRAIN images [Draft review plan](../manifests/CCIHP_QUALITY_REVIEW_PLAN_V1.json), [decision](CIHP_GROUND_TRUTH_RECOVERY_DECISION.md)

## 9. Executed tests / limitations

New GT reader **8/8 synthetic tests PASS**, actual 30-frame source roundtrip PASS; lossless diagnostic NPZ export3cases passes reload (`allow_pickle=False`) Preserves instance dtype/unknown IDs/unassigned regionsและrejects silent overlap flattening Tests ไม่เป็น scientific quality/benchmark scores

First auditหยุดเมื่อพบ undocumented22 หลัง CRCครบ และ JSON exportเคยติด NumPy bool; เก็บ failure recordsและแก้ checker/exportใน studycodeเท่านั้น Resume verified CRC ledger ไม่รัน full CRCซ้ำ ไม่แก้ sourcePNG/third-party evaluator

**Overall Stage 0 still BLOCKED / WAITING_FOR_USER_APPROVAL.** ไม่มี full benchmark, parser/checkpoint download/inference, training, hybrid, attributes, PPSS หรือ CCTV activity
''')

imgs={x['image_id']:x['diagnostic_image'] for x in cross['cases'] if x.get('diagnostic_image')}
publish('reports/CCIHP_PERSON_INSTANCE_VERIFICATION.md',f'''# CCIHP Person Instance Verification — Stage 0E Continuation

**Sample structural/lossless fidelity: PASS_WITH_WARNINGS. Dataset-wide physical correctness: NOT_VERIFIED. Native CIHP target equivalence: BLOCKED.** Source is actual `datasets/CCIHP_icip.zip`; previous missing-source report archived

## What ran

30 frames: 25 TRAIN + 5 VAL integrity-only; native maps90 decode/CRC/dimensions PASS; **96 image-local human IDs / 840 attribute instances**, every sampled attribute instance has exactly one human and semantic class. Per-person canonical view preserves full source human support, semantic categories (including unknown22), uint16 attribute IDs, original dimensions, source hashes and unassigned regions; reconstruct all three original maps **30/30 exact**

Human labels identify source-defined people inside each image; no temporal identity claim or automatic guarantee one physical person per ID across the dataset. Source map can store only one owner at each pixel; no recovered hidden/amodal masks or inferred neighboring person identity

## Case 1 — Nearby people control: 0002190

![CCIHP same-frame human/category comparison](../{imgs['0002190']})

Observation: foregroundสองคนถูกแยก Human IDs1/2, boundaries align with visible image regions; CIHP/CCIHP semantic panelsใกล้กัน แต่ raw categoriesต่าง361pixelsและ FG/BGต่าง7pixels

Interpretation: demonstrates useful local person ownership even where global semantics look similar; equality of visual appearance is not native-human equivalence Original native Human_ids unavailable, so cannot certify original person mask/order/completeness

## Case 2 — Crowded foreground: 0005008

![CCIHP group comparison](../{imgs['0005008']})

Observation: Human IDs1–7 separate the seven dominant foreground people. Source DatasetNinjaมี53part objects;52อยู่ในหนึ่ง humanครบsupportและ1ทับหลาย human IDs มองเห็น background peopleด้วยแต่ source completeness policyยังไม่verified

Interpretation: physical alignmentของforegroundตัวอย่างนี้ช่วยสนับสนุนcustom GT usefulness แต่ mixed-source native CIHP object-to-person associationยังไม่lossless/unambiguous ห้ามแก้เป็น majority ownerแล้วเรียก original native GT

## Case 3 — Clothing/accessory boundary changes: 0012008

![CCIHP garment comparison](../{imgs['0012008']})

Observation: Human IDs1–3 separate dominant foreground people; originalRGB panelregionเดียวกัน Category panels visibly differ over upper garments/accessory regions. Raw differences46,665pixels; FG/BGdifferences4,905pixels. Of30 CIHP part objects,29have one complete owner and1covers multiple CCIHP human IDs

Interpretation: annotation definitions/region edits change evaluation target despite same source image ไม่ตีความว่า parserแม่นขึ้น/แย่ลง เพราะไม่มี parser inference หรือ independent truth adjudication

## Coverage and unresolved conventions

Sampled category-foreground outside humans0pixels; attribute-instance outside humans0; human support without category12pixelsใน3images ไม่เติมlabelsหรือเรียกerrorอัตโนมัติ TRAIN0033810มี2pixelsค่า22นอกdocumented inventory; retain values/hash/coordinates

Visible-person completeness, actual occlusion/overlap policyและannotation-error prevalence **NOT_VERIFIED** Shared clothes/adjacent peopleไม่เป็นproof annotation error Two single-valued maps cannot provide amodal overlap ground truth; no GT masks reconstructed with YOLO or grouping heuristics

[Full evidence](../{str((RUN/'BOUNDED_CROSS_DATASET_COMPARISON.json').relative_to(ROOT))}), [fidelity](../{str((RUN/'CCIHP_GT_FIDELITY.json').relative_to(ROOT))}), [main audit](CCIHP_CIHP_COMPATIBILITY_AUDIT.md)
''')
publish('reports/CIHP_GROUND_TRUTH_RECOVERY_DECISION.md', '''# CIHP Ground Truth Recovery Decision — Actual CCIHP Available

**Decision B — PARTIALLY_COMPATIBLE.** Previous Decision C was for the earlier available TAR only; historical reports and fingerprints preserved

| Target | Result with current ZIP + TAR | Scientific limit |
|---|---|---|
| Original native CIHP per-person GT | BLOCKED | Modified CCIHP masks/taxonomy;21mixed-owner and26partly unassigned cross-source objects in30samples; no original Human_ids reference |
| CCIHP-native per-person parsing | CONDITIONAL | Human/category/instance filescomplete;30sample roundtrip verified; global quality/unknown22/rights/cohort definitionspending |
| Body/clothing common-class benchmark | CONDITIONAL | Possible underexplicit shared GT projection; no automatic Dress recovery or unsupported->background |
| Supported accessory diagnostics | CONDITIONAL | Bag/Others/FaceMask differ from native CIHP and parser capacities; needs representability/cohort denominators |
| Native CIHP APp/PCP-equivalent benchmark | NOT_VERIFIED | Same images/classes-by-name are insufficient; do not relabel custom scores official |

## Recommended route and approval

Recommend **first review a separate custom CCIHP-person body/clothing GT track using existing CIHP RGB**, then Full Quality Audit if approved. This can resolve useful per-person preparation without another dataset download, while keeping native CIHP reference separate. It does not freeze primary dataset, shared taxonomy or evaluator thresholds

If the study requires original CIHP official/native target comparability, obtain verified native GT-only supplement/local native copy; otherwise official original distributionrequires separate acquisition approval. CCIHP cannot automatically replace that source. Do not download DatasetNinja again

Additional CCIHP GT passes file-integrity/paired-ID gates, but does not resolve all dataset quality issues. Next bounded work should investigate unknown22 at two pixels,12human-without-category pixels, publication/release class definitions, visible-person/ignore policy and RGB/native-reference limits; no automatic repairs or exclusions. Then independently review ~200 stratified TRAIN images with complete source audit under agreed cohort

Keep imageset denominators separate: CCIHP train28,280 / val5,000 annotated IDs pairexactly with CIHP TAR; person counts96only for audited30images, full person total NOT_COMPUTED. Existing39train–valexact-byte duplicategroupsremain disclosed; no silent split changes/sensitivity activation

CCIHP native-class mapping remains DRAFT; source semantic details and rights remain separate from original CIHP RGB/GT and model terms. CC-BY-NC annotationtermscompatible with Decision5A subject to terms; original RGB permissionstillunverified. CompanyCCTV, colors/patterns/size evaluation and parser benchmarksremainoutside this audit

[Compatibility audit](CCIHP_CIHP_COMPATIBILITY_AUDIT.md), [person evidence](CCIHP_PERSON_INSTANCE_VERIFICATION.md), [matrix](../taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv), [quality-review proposal](../manifests/CCIHP_QUALITY_REVIEW_PLAN_V1.json)

**STOP — WAIT FOR USER APPROVAL.** No additional dataset acquisition, Stage1, full benchmark or inference
''')

save('manifests/CCIHP_QUALITY_REVIEW_PLAN_V1.json',{'schema_version':'1.0','status':'DRAFT_AWAITING_TRACK_AND_FULL_QUALITY_APPROVAL',
      'candidate_track':'CUSTOM_CCIHP_PERSON_BODY_CLOTHING_NOT_OFFICIAL_CIHP','dataset_zip':'datasets/CCIHP_icip.zip',
      'rgb_source':'datasets/cihp-DatasetNinja.tar','target_human_review_images':200,'review_split':'Training',
      'seed':20261012,'sample_IDs_frozen':False,'validation_used_for_policy_tuning':False,
      'selection_requires_verified_global_train_statistics':True,
      'strata':['GT Human_ids person counts','image resolution','human area/occupancy','person scale variation',
                'rare semantic concepts','adjacent people/crowding based on observable geometry'],
      'independent_random_core_required':True,'anomaly_selected_examples_separate_from_prevalence_estimation':True,
      'review_categories':['Pixel/RGB alignment','one physical person per ID','person coverage policy','class semantic consistency',
                           'accessory support','unknown labels/void','confidence of reviewer interpretation'],
      'review_outcomes':['CONFIRMED_CONSISTENT','CONFIRMED_ERROR','SUSPECTED_ANOMALY','UNCERTAIN_POLICY','NOT_REVIEWABLE'],
      'full_quality_audit_authorized':False,'source_relabel_or_exclusion_authorized':False,'primary_promotion_authorized':False})

amendment='''\n## Current Stage 0E continuation — actual CCIHP ZIP available

The newly transferred `datasets/CCIHP_icip.zip` is now present: all-member ZIP CRC/SHA inventory PASS; all6annotation folderspair28,280TRAIN/5,000VAL IDsexactly with CIHP TAR. Bounded30images/96humanIDs lossless reconstructionpasses;3full-frameGTcomparisonsinspected

**Decision B — PARTIALLY_COMPATIBLE** supersedes the earlier missing-input Decision C for the newly available assets. CCIHP own-person GT can support a proposed custom body/clothingtrackafter Full Quality Audit/rights/common-domainreview. It is not verified original native CIHP: modifiedsemantics/masks and21multi-human+26partly unassigned CIHPobjects prevent automatic substitution. Unknown Category22(2pixels) and12human/categorygap pixels need clarification; no sourcefix/exclusion

[Current audit](CCIHP_CIHP_COMPATIBILITY_AUDIT.md), [GT decision](CIHP_GROUND_TRUTH_RECOVERY_DECISION.md), [versioned evidence](../provenance/CCIHP_ARCHIVE_AUDIT_V2.json). Full Quality Audit/200TRAINreview still unapproved, taxonomy/primaryroles stilldraft; no download/inference/attributes/PPSS/CCTV
'''
for name in ['reports/CIHP_QUALITY_AUDIT.md','reports/PRIMARY_DATASET_DECISION.md','reports/STAGE0_NEXT_ACTIONS.md']:
    text=(ROOT/name).read_text()
    text=text.replace('## Stage 0E — Actual archive identity and person-GT recovery','## Historical Stage 0E — before CCIHP transfer')
    text=text.replace('## Stage 0E compatibility amendment','## Historical Stage 0E compatibility amendment — before transfer')
    text=text.replace('## Stage 0E — GT-source decision ที่ตรวจแล้ว','## Historical Stage 0E — before actual CCIHP transfer')
    first,rest=text.split('\n',1)
    publish(name,first+'\n\n**Current update:** Actual CCIHP ZIP now audited; **B — PARTIALLY_COMPATIBLE**. See current Stage0E section below; earlier missing-source notes are historical.\n'+rest+amendment)
readme=(ROOT/'README.md').read_text()
start=readme.index('## Stage 0E — CCIHP / native CIHP compatibility')
readme=readme[:start]+'''## Stage 0E — actual CCIHP / native CIHP compatibility

[Current audit](reports/CCIHP_CIHP_COMPATIBILITY_AUDIT.md), [person-GT verification](reports/CCIHP_PERSON_INSTANCE_VERIFICATION.md), [decision](reports/CIHP_GROUND_TRUTH_RECOVERY_DECISION.md), [matrix](taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv), [V2 evidence](provenance/CCIHP_ARCHIVE_AUDIT_V2.json).

Actual CCIHP ZIP now available; all-member CRC/SHAinventoryPASS.30pairedframes/96sourcehumanIDs roundtripPASS;3GTcomparisons. **B—PARTIALLY_COMPATIBLE:** custom CCIHP-persontrackconditional on quality/rights/taxonomyreview; original native CIHP equivalenceBLOCKED. Unknownlabel22 and cross-source ownership conflictsretained. No acquisition/model/benchmark/attributes/CCTV/PPSS. Primaryroles/commonmappingremainDRAFT; FullQualityAuditrequiresapproval
'''
publish('README.md',readme)
state=json.loads((ROOT/'STUDY_STATE.json').read_text())
state['last_updated_utc']=NOW
state['stage0e_ccihp_cihp']={'run_id':active['run_id'],'status':'PASS_WITH_WARNINGS_BOUNDED_AUDIT_ONLY',
       'ccihp_source_present':True,'archive_integrity':'PASS','native_CCIHP_person_fidelity':'PASS_30_CASES',
       'custom_CCIHP_GT_feasibility':'CONDITIONAL_FULL_QUALITY_REVIEW','native_CIHP_GT_equivalence':'BLOCKED',
       'decision':'B_PARTIALLY_COMPATIBLE','unknown_label22_pixels_sample':2,'primary_promoted':False,
       'full_quality_audit_started':False,'download_started':False,'benchmark_started':False,
       'evidence':'provenance/CCIHP_ARCHIVE_AUDIT_V2.json','report':'reports/CCIHP_CIHP_COMPATIBILITY_AUDIT.md',
       'validation':'provenance/CCIHP_STAGE0E_NATIVE_VALIDATION_V2.json','review_gate':'WAIT_FOR_USER_APPROVAL'}
save('STUDY_STATE.json',state)
save('provenance/CCIHP_STAGE0E_NATIVE_DOCUMENT_REVISIONS_V2.json',{'run_id':active['run_id'],'revisions':revisions,'new_artifacts':created})
print(json.dumps({'decision':'B','bounded_audit':'PASS_WITH_WARNINGS','native_CIHP_equivalence':'BLOCKED',
                  'archived_documents':len(revisions),'matrix_rows':len(matrix),'actual_inference':0}))
