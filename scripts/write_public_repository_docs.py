"""Write publication-only navigation and derived summaries, without changing benchmark evidence."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import json
import hashlib

S = Path(__file__).resolve().parents[1]
P = S.parent / 'Human_Parsing_Study_Public'
R = 'provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z'
RUN = Path(R).name


def text(name, value):
    path=P/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(value.strip()+'\n')


def js(name, value):
    text(name,json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False))


def main():
    if (P/'README.md').exists():
        raise SystemExit('Publication documents already exist; preserve them and review an explicit revision instead of overwriting.')
    final=json.loads((S/R/'FINAL_BENCHMARK_VALIDATION.json').read_text())
    assert final['status']=='FINISHED_WITH_INCOMPLETE_SYSTEMS'
    metric=f'metrics/{RUN}'
    reference=f'{R}/execution_restored_detector_v1'
    config='configs/application_v2_first_cohort_v12.yaml'
    decision='provenance/APPLICATION_V2_DECISIONS_V11.json'
    mapping='taxonomy/APPLICATION_BODY_CLOTHING_CPI_ACCEPTED_V3.json'
    components=final['components']
    table='| Component | Frames | COMPLETE | FAILED | INVALID |\n|---|---:|---:|---:|---:|\n'
    for row in components:
        table+=f"| {row['component']} | {row['frames']:,} | {row['complete']:,} | {row['failed']:,} | {row['invalid']:,} |\n"
    text('README.md',f'''# Human Parsing Study

Independent noncommercial student academic research on pretrained body/clothing parsing and supported accessories. Frozen YOLO26x-Seg supplies person opportunities for the first **T3b** cohort; native parsers also infer their own instances. This is a post-run publication snapshot, not the Git revision used at launch.

**Latest run: `{RUN}` — FINISHED_WITH_INCOMPLETE_SYSTEMS.** No main accuracy winner is available under STRICT_COMPLETE. The two systems remain in every result table; missing main scores are null, never zero.

{table}
The 565 native failures are CUDA OOM; one ConvNeXt-B image is an unresolved interrupted output. Inference was shared across reference **5,000** and main **4,961** memberships; it was not run twice for two tables. Both systems are INCOMPLETE in both populations and at matching IoU 0.50/0.75. This is quality-only: no timing, FPS or VRAM ranking.

## Start here

| Document | Canonical responsibility |
|---|---|
| [REPORT.md](REPORT.md) | Technical account of the completed attempt and retained limitations |
| [RESULTS_SUMMARY_TH.md](RESULTS_SUMMARY_TH.md) | Compact numerical quick summary in Thai |
| [PRESENTATION_SUMMARY_TH.md](PRESENTATION_SUMMARY_TH.md) | Presentation narrative, operational visual evidence and interpretation limits |
| [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) | Exact first-cohort procedure and executable authority |
| [DATASET_DETAILS.md](DATASET_DETAILS.md) | Dataset roles, populations, GT domains and taxonomy distinctions |
| [DATA_SCHEMA.md](DATA_SCHEMA.md) | Columns, metric formulas, denominators and missing values |
| [STUDY_STANDARD.md](STUDY_STANDARD.md) | Scientific and operational invariants |
| [HANDOFF.md](HANDOFF.md) / [AGENTS.md](AGENTS.md) | Continuation instructions and prohibited actions |
| [SETUP.md](SETUP.md) / [REPRODUCIBILITY.md](REPRODUCIBILITY.md) | Portable checks versus asset-dependent reproduction |
| [ARTIFACTS.md](ARTIFACTS.md) | Public metadata versus local/restricted assets |
| [History index](reports/HISTORY_INDEX.md) | Current and superseded evidence, without rewriting past knowledge |

## Machine-readable results

- [Quality results]({metric}/QUALITY_RESULTS.csv): 8 rows, all INCOMPLETE with blank main metrics.
- [Failure inventory]({metric}/FAILURES.csv): 566 component-image failure/invalid rows, zero retries.
- [Operational success-only diagnostics]({metric}/OPERATIONAL_SUCCESS_ONLY_DIAGNOSTICS.csv): not main scores and not a ranking on unequal successful populations.
- [Current study state](STUDY_STATE.json), [run manifest](cohorts/first_cpi_t3b/RUN_MANIFEST.json), [model inventory](inventory/MODEL_INVENTORY.csv).
- [Source/config copy manifest](publication/SOURCE_COPY_MANIFEST.json), [benchmark validation]({R}/FINAL_BENCHMARK_VALIDATION.json), [server post-export checks]({R}/POST_EXPORT_VERIFICATION.json).

## Reproduction boundary

Clone alone permits the documented portable CPU/synthetic checks and verification of released result summaries. It does **not** provide datasets, checkpoints, native CUDA environments, pixel GT, saved masks/logits or all GT context bindings. See [external artifacts](ARTIFACTS.md). Frozen config flags document the historical approval for this one run; they do not authorize a new run.

No company CCTV, source dataset photos, native model source trees, weights or bulk predictions are included. No new benchmark, download or GPU smoke is performed to prepare this repository. Public GitHub publication is pending a separate user decision; no public URL exists yet.
''')
    text('STUDY_STANDARD.md',f'''# Human Parsing Study — Current Scientific Standard

This document governs the current first-cohort record. Earlier Stage 0 standards are preserved [byte-identically](reports/archive/pre_public_snapshot/STUDY_STANDARD.md). They must not override later accepted, hash-bound decisions.

1. Original datasets, the completed YOLO study, weights and working environments are immutable.
2. Runner/evaluator values come from [{config}]({config}), bound to [{decision}]({decision}). File version numbers alone are not evidence of acceptance. Original V11 launch and V12 detector-infrastructure restoration freezes are separate from any Git snapshot/tag.
3. Scope is exactly CPI_R50_CIHP and CPI_ConvNeXtB_CIHP plus frozen YOLO26x, T3b FP32. Reference 5,000 inference jobs per component support separate main 4,961 and reference 5,000 reports. No post-hoc membership changes.
4. STRICT_COMPLETE requires full eligible-population completion for main metrics. INCOMPLETE rows and operational diagnostics stay visible. Valid empty output is successful execution and incurs the applicable GT misses. No failed-image retries were authorized.
5. Native identity and YOLO opportunity identity remain separate, and T3b records retain both. A semantic adapter's final person output does not establish native instance capability. Unsupported native count is null; a supported empty count is zero.
6. Prediction-only association IoU 0.50 is distinct from final prediction-to-GT bbox matching 0.50/0.75. GT never conditions parser inference or deployment ownership.
7. Mapping confidence remains ACCEPTED_WITH_INDIRECT_EVIDENCE, not DIRECT_VERIFIED. Unsupported GT is not silently background; known-target/owner-unknown pixels can contribute globally but are void per person.
8. Source track, model/checkpoint/config, input geometry, taxonomy, GT domain and population bindings must be explicit. Retain native hard labels losslessly; logits are unavailable unless actually exported.
9. No tuning on validation. Quality-only findings cannot support FPS/VRAM rankings, architecture causality, statistical significance, CCTV robustness, tracking performance or deployment readiness.
10. Preserve failed/interrupted records and historical reports. Scoped continuation/restoration is not a general certified workflow-resume or cached-rescoring feature.
11. A public Git snapshot created after execution is not a launch commit. Human review of independent annotation quality is distinct from automated integrity checks and assistant visual inspection.
12. A new configuration, precision, population, inference pass, model download, training, hybrid or CCTV experiment requires separate explicit authorization. This repository grants none.

Dataset, person sources, adapters, canonical prediction records, taxonomy, evaluator, resource measurement and interpretation remain separate layers. [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) is the procedure; [DATA_SCHEMA.md](DATA_SCHEMA.md) is the interface.
''')
    text('EXPERIMENT_PROTOCOL.md',f'''# First CPI T3b Cohort — Executed Protocol

Run `{RUN}`. Source of executable values: [V12 config]({config}) / [Decision V11]({decision}); original [V11 launch freeze]({R}/FREEZE.json), [restored-profile freeze]({R}/RESTORED_PROFILE_FREEZE.json). V12 retains the accepted scientific values and resolves a pre-model shared-detector environment failure; it does not alter native CPI settings.

| Item | Executed setting |
|---|---|
| Systems | CPI_R50_CIHP; CPI_ConvNeXtB_CIHP |
| Person dependency | Frozen YOLO26x-Seg |
| Track / precision | T3b / FP32, autocast=False, TF32=False |
| RGB | Existing CIHP DatasetNinja TAR images, byte/decode hashes and original dimensions verified |
| GT | CCIHP released Category_ids + Human_ids + Instance_ids, original grid |
| Inference population | Reference Validation 5,000 ordered IDs, once per component |
| Reports | Main 4,961 and reference 5,000, separate population bindings |
| YOLO | imgsz=640; conf=0.25; NMS IoU=0.70; max_det=200; retina_masks=True |
| Native CPI score thresholds | R50=0.01; ConvNeXt-B=0.05 |
| Association | Predicted YOLO bbox ↔ native parser bbox; IoU ≥0.50; no GT |
| Final GT matching | Native parser bbox ↔ eligible GT localization bbox; IoU ≥0.50 primary / ≥0.75 secondary |
| Assignment | One-to-one, eligible cardinality then IoU; immutable IDs then pinned SciPy tie behavior |
| Coordinates | Original image, XYXY half-open; conditioning bbox distinct from evaluation bbox |
| Target / domain | Six-foreground CPI-only mapping; released-annotation-relative GT domain |
| Completeness | STRICT_COMPLETE; no failed-image retries or score-dependent exclusions |
| Resource claims | Quality-only; no clean repeated timing or cost rankings |

Native CPI runs full frames using its released architecture/internal detector; it is not cropped or silently stripped of detection overhead. The final T3b persons are prediction-only associated to YOLO opportunities. Native unmatched instances and opportunity identities are retained as provenance; final GT matching happens after that association.

RGB/GT and source hashes are checked independently. Native outputs are lossless masks/boxes. The same inference artifacts support two report populations only against their exact matching-view/context bindings.

## Execution deviations retained as evidence

The first YOLO worker aborted before model import/image inference when config validation imported unavailable SciPy in the YOLO environment. The approved scientific settings were preserved; CPU authorization was separated from the detector bootstrap without modifying packages. YOLO then completed 5,000 images once.

R50 completed 4,475 and failed 525 CUDA-OOM images. ConvNeXt-B initially committed 3,779 rows; image 0034896 had an incomplete NPZ and remains INVALID/UNRESOLVED_INTERRUPTION. Exactly 1,220 never-attempted images continued with unchanged settings, yielding a combined 4,959 complete / 40 OOM / 1 invalid. Original ledgers and partial bytes remain external and unmodified. This is not a retry of failed images.

## Evidence and reproduction limits

[Technical results](REPORT.md), [population manifest](cohorts/first_cpi_t3b/POPULATIONS.json), [data contract](DATA_SCHEMA.md), [external dependencies](ARTIFACTS.md). The archived settings include legacy preparation fields; the historical validation execution uses `first_cohort.execution_spec` and `validation_launch`, not the old 20-variant inventory or bounded-TRAIN roster. Do not infer permission from a historical full_benchmark flag or relaunch an old orchestrator.
''')
    text('DATASET_DETAILS.md',f'''# Dataset Details and Evaluation Populations

## Current cohort and other dataset roles

The first cohort uses **CCIHP-derived custom person-level body/clothing GT** with corresponding CIHP DatasetNinja RGB. It is not an original native CIHP benchmark. MHP-v2 remains a provisional secondary fine-grained resource; a universally clean/primary dataset or application-wide taxonomy is not declared. PPSS is paused. No company CCTV is included or processed here.

| Asset | Local workspace-relative path | Content / public status |
|---|---|---|
| CCIHP annotation ZIP | datasets/CCIHP_icip.zip | 28,280 TRAIN and 5,000 VAL Category/Human/Instance annotation sets; RGB absent; external |
| DatasetNinja CIHP TAR | datasets/cihp-DatasetNinja.tar | Corresponding RGB/converted parts; it alone lacks native person ownership GT; external |
| MHP-v2 | datasets/LV-MHP-v2/ | Per-person parsing planes; original dataset/splits untouched; external |

Archive sizes/SHA256 and access limitations are in [ARTIFACTS.md](ARTIFACTS.md). The CCIHP conversion is PARTIALLY_COMPATIBLE with CIHP, not VERIFIED_NATIVE_COMPATIBLE. Automated label/dimension/ownership-association checks do not prove that every physical person/class boundary is annotated correctly. Human-review and assistant-review evidence are distinguished in the historical reports.

## Frozen first-cohort populations

| Population | Images | G_loc | G_sem | Role |
|---|---:|---:|---:|---|
| main | 4,961 | 17,434 | 17,390 | Exact source-overlap-controlled membership |
| reference | 5,000 | 17,548 | 17,504 | Original released validation population |

The main excludes the predeclared 39 train/validation JPEG-byte overlap members, not failures discovered after inference. Controlled membership is not proof of no near duplicates or checkpoint training exposure. The two populations overlap and are not independent samples. Image IDs and denominators remain traceable through [population metadata](cohorts/first_cpi_t3b/POPULATIONS.json) and the original bound config/manifests. GT pixel arrays and detailed person-binding artifacts remain external.

## Semantic and ownership policy

CCIHP Category0/Human0 is outside the annotated person foreground; domain rules come from accepted released annotations, not from predictions. Known semantic target with Human0 is globally usable but per-person VOID_OWNER_UNKNOWN. Human-positive/category0 is unresolved semantic support and is void semantically under the accepted recipe. Unknown22 and unsupported target concepts are explicitly void, never silently background. All original values and identities are preserved.

The native CCIHP taxonomy differs from CIHP: for example CIHP ID6 is Dress while CCIHP ID6 is Face Mask. CIHP/LIP ID10 also differs (torso skin versus jumpsuit). The explicit [accepted mapping]({mapping}) produces BG0 and Face region1, Exposed torso2, Exposed arms3, Exposed legs4, Coarse garments5 and Footwear6. Display name Face region does not change numeric ID1. Accessories outside this cohort are unsupported, not evaluated as if predicted by all models.

G_loc and G_sem are declared GT eligibility sets; G_sem is a subset of G_loc. GT masks may overlap and keep instance identity. Localization boxes are GT-body support under the frozen policy, not arbitrary anatomical silhouettes from all carried-object classes. FP/FN are relative to released annotations; FP does not prove that a physical person is absent.

## Earlier MHP-v2 limitations

The four original defective JPEGs remain immutable. Approved readable views contain 15,400 TRAIN, 4,999 VAL/13,257 GT persons, and exact-overlap-controlled readable VAL 4,347/11,408 persons. These are not an unqualified official 5,000-image result. Exact RGB duplication and uncertain GT ownership remain separate limitations; this cohort computes no MHP-v2 validation score.
''')
    text('REPORT.md',f'''# First CPI T3b Cohort — Technical Report

## Status and scope

`{RUN}` is **FINISHED_WITH_INCOMPLETE_SYSTEMS**. This describes terminal execution and reporting, not successful accuracy completion. Both CPI systems are INCOMPLETE in main/reference at IoU0.50/0.75. No main quality winner exists.

The objective is pretrained body/clothing parsing conditioned by frozen YOLO opportunities, without training or validation tuning. [Protocol](EXPERIMENT_PROTOCOL.md), [dataset/domain](DATASET_DETAILS.md) and [schema](DATA_SCHEMA.md) are canonical for those topics.

## Observed execution

{table}
565 CUDA OOM failures and one unresolved interrupted native output remain in the [failure CSV]({metric}/FAILURES.csv). Main complete frames are R50 **4,436/4,961** and ConvNeXt-B **4,920/4,961**; all 566 noncomplete component-images belong to main as well as reference. No population was altered based on these outcomes.

## Canonical score tables

[QUALITY_RESULTS.csv]({metric}/QUALITY_RESULTS.csv) contains exactly 8 rows: two systems × two populations × two matching views. Main metrics are blank CSV fields / JSON null, with `main_score_eligible=false` and `status=INCOMPLETE`. Null does not mean zero accuracy. The four source reports retain all denominators and failure diagnostics:

- [Main primary]({reference}/MAIN_PRIMARY_REPORT.json), [main secondary]({reference}/MAIN_SECONDARY_REPORT.json).
- [Reference primary]({reference}/REFERENCE_PRIMARY_REPORT.json), [reference secondary]({reference}/REFERENCE_SECONDARY_REPORT.json).

[Success-only diagnostics]({metric}/OPERATIONAL_SUCCESS_ONLY_DIAGNOSTICS.csv) are conditional on different successful subsets, and cannot replace primary scores or rank the two systems. No new per-target score table is invented: the released aggregate reporter did not publish a completed-population target leaderboard; hard-label predictions and detailed scoring evidence stay external.

## Interpretation and limitations

**Observation:** Native FP32 paths encountered different numbers of OOM failures under their declared, different native score thresholds. YOLO completed every input. **Interpretation:** These are configuration/resource feasibility findings, not evidence of semantic accuracy or backbone causality. A successful three-image TRAIN smoke did not certify completion on every validation input.

This is custom CCIHP coarse body/clothing evaluation, not official CIHP AP or mIoU. Mapping remains ACCEPTED_WITH_INDIRECT_EVIDENCE. Training exposure differs across inventory checkpoints. Controlled membership is not universal leakage clearance; released GT is not complete physical-person truth. No significance, CCTV robustness, tracking, latency/FPS/VRAM winner or commercial deployment conclusion is made.

## Integrity and provenance

[Server final validation]({R}/FINAL_BENCHMARK_VALIDATION.json) and [independent export checks]({R}/POST_EXPORT_VERIFICATION.json) verify rows/bindings, retained 566 failure records, null main metrics, 126 protected-file hashes and unchanged YOLO repository statuses. Archived CPU application tests passed **151**; that is not a claim that 151 portable tests run from a public clone or that inference completed successfully.

The [dated executed report](reports/FIRST_COHORT_T3B_BENCHMARK_REPORT_TH_20261019.md) is retained unchanged. [Run manifest](cohorts/first_cpi_t3b/RUN_MANIFEST.json) distinguishes original V11 freeze, V12 infrastructure restoration, source/checkpoint/environment hashes and the later public Git snapshot. [Reproducibility](REPRODUCIBILITY.md) lists missing external assets and tested clean-checkout boundaries.

## Visual and presentation evidence

[PRESENTATION_SUMMARY_TH.md](PRESENTATION_SUMMARY_TH.md) explains operational visual evidence without duplicating this numerical table. Actual dataset photos and saved-mask overlays are not redistributed without verified image/annotation rights; no synthetic image is substituted for benchmark visual evidence.

## Stop condition

This run is closed. A resource correction, new precision, inference retry or broader roster is a new configuration/authorization decision. No further experiment starts automatically.
''')
    text('RESULTS_SUMMARY_TH.md',f'''# สรุปผล Human Parsing — CPI T3b กลุ่มแรก

## สรุปใน 1 นาที

- เปรียบเทียบ CPI_R50_CIHP และ CPI_ConvNeXtB_CIHP กับ frozen YOLO26x ใน T3b / FP32 ไม่มี fine-tuning
- Reference 5,000 ภาพ ใช้ inference ครั้งเดียวต่อ component แล้วรายงาน main 4,961 ภาพแยกตาม membership
- Matching 0.50 หลัก / 0.75 เสริม และ STRICT_COMPLETE ตามกติกาที่รับรองไว้
- YOLO สำเร็จ 5,000 ภาพ; R50 สำเร็จ 4,475; ConvNeXt-B สำเร็จ 4,959
- R50 พบ CUDA OOM 525 ภาพ; ConvNeXt-B พบ OOM 40 และ interrupted/invalid 1 ภาพ
- **ทั้งสองระบบ INCOMPLETE จึงไม่มีคะแนนหลักและยังไม่มี accuracy winner**; ไม่ใช้ success-only จัดอันดับ
- เป็น quality-only ไม่มีผู้ชนะด้านเวลา FPS หรือ VRAM

## ผลลัพธ์หลัก

| Population | ระบบ | สำเร็จ | Failed / Invalid | G_loc / G_sem | คะแนนหลัก |
|---|---|---:|---:|---:|---|
| main | CPI R50 | 4,436 / 4,961 | 525 / 0 | 17,434 / 17,390 | N/A — INCOMPLETE |
| main | CPI ConvNeXt-B | 4,920 / 4,961 | 40 / 1 | 17,434 / 17,390 | N/A — INCOMPLETE |
| reference | CPI R50 | 4,475 / 5,000 | 525 / 0 | 17,548 / 17,504 | N/A — INCOMPLETE |
| reference | CPI ConvNeXt-B | 4,959 / 5,000 | 40 / 1 | 17,548 / 17,504 | N/A — INCOMPLETE |

จำนวน execution เหมือนกันที่ matching 0.50 และ 0.75; [CSV canonical]({metric}/QUALITY_RESULTS.csv) เก็บครบ 8 แถว N/A ไม่ใช่คะแนนศูนย์

## สิ่งที่ตัวเลขบอกเรา

- Configuration ของ native CPI ทั้งสองยังรันไม่ครบประชากรบน T4 ในรอบนี้ แม้ bounded TRAIN integration เคยผ่าน
- R50 และ ConvNeXt-B สำเร็จต่างกัน 484 ภาพใน reference แต่ตัวเลขนี้ไม่ใช่ผลต่าง accuracy
- ทั้ง 566 failure/invalid component-image rows อยู่ใน main ด้วย การตัด 39 overlap members จึงไม่ได้ทำให้ระบบใด COMPLETE
- Main/reference เป็นชุดภาพซ้อนกัน ไม่ใช่การทดสอบอิสระสองรอบ และไม่มี inference ซ้ำเพื่อสร้างตารางแยก

## ข้อจำกัดและรายละเอียด

Mapping เป็น ACCEPTED_WITH_INDIRECT_EVIDENCE; GT เป็น released-annotation-relative; เป็น custom CCIHP coarse targets ไม่ใช่ official CIHP benchmark และยังไม่ยืนยัน CCTV robustness

[REPORT.md](REPORT.md) · [การนำเสนอและหลักฐานภาพ](PRESENTATION_SUMMARY_TH.md) · [Failures]({metric}/FAILURES.csv) · [Data schema](DATA_SCHEMA.md)
''')
    text('PRESENTATION_SUMMARY_TH.md',f'''# Human Parsing — หลักฐานและการตีความของกลุ่ม CPI T3b

## 1. คำถามที่กำลังตอบ

เราต้องการคัดระบบ parsing สำหรับ body/clothing ภายใต้ frozen YOLO26x รอบนี้ทดสอบสอง CPI configurations ที่มี native instance parser การทดลองจบแล้ว แต่ยังไม่มีคะแนนหลักครบประชากร จึงยังเลือกผู้ชนะด้าน semantic accuracy ไม่ได้ ดูตัวเลขแบบสแกนเร็วที่ [RESULTS_SUMMARY_TH.md](RESULTS_SUMMARY_TH.md)

## 2. ระบบทำงานอย่างไร

```mermaid
flowchart TD
  A[RGB frame] --> Y[Frozen YOLO26x opportunities]
  A --> P[Native CPI full-frame instances]
  Y --> J[Prediction-only bbox association IoU 0.50]
  P --> J
  J --> O[Final persons: retain YOLO and native identities]
  O --> E[GT bbox matching 0.50 / 0.75 and common parsing scoring]
  G[Released CCIHP GT and frozen domain] --> E
```

GT ใช้ในการประเมินหลังทำนาย ไม่ใช่ input ของ YOLO/CPI การมีสอง identity ไม่ได้หมายความว่าใช้ GT bbox หรือบังคับให้ทุก native prediction ผ่าน YOLO

## 3. หลักฐานภาพที่เผยแพร่ในรอบนี้

![Observed completion and failures](plots/first_cohort_completion.png)

กราฟนี้สร้างจาก ledger-derived canonical counts เป็น **operational evidence** ไม่ใช่ภาพ mask และไม่ใช่ accuracy ranking สีของ failures แสดงจำนวนงานที่ไม่สำเร็จภายใต้ configuration เดิม ภาพ RGB/GT/overlay จริงยังอยู่ภายนอกตาม [artifact policy](ARTIFACTS.md); ยังไม่ยืนยันสิทธิ์แจกจ่ายภาพบุคคล จึงไม่นำภาพมาใส่ public หรือใช้ภาพสร้างขึ้นแทนข้อมูลจริง

## 4. Failure Analysis

**Observation:** YOLO สำเร็จครบ ขณะที่ native CPI พบ CUDA OOM ภาพ 0034896 ของ ConvNeXt-B มีไฟล์ NPZ ที่เขียนไม่สมบูรณ์และคง INVALID/UNRESOLVED_INTERRUPTION ไว้ กระบวนการเดิมหยุดโดยไม่มี terminal manifest จึงไม่อ้างสาเหตุการหยุดเกินหลักฐาน

**Interpretation:** ปัญหาอยู่ที่ความครบของเส้นทาง native configuration/resource ไม่ได้แสดงว่า mask ของโมเดลใดแม่นต่ำกว่า การเปลี่ยน precision, threshold หรือ chunking หลังดู VAL เพื่อให้ผ่านจะเป็น configuration ใหม่และต้องพิจารณาแยก

**ขอบเขต:** OOM counts ไม่ใช่ peak VRAM benchmark และ smoke latency ไม่ใช่ clean timing ไม่มีการจัดอันดับต้นทุนจากกราฟนี้

## 5. ทำไมไม่เฉลี่ยเฉพาะภาพที่ผ่าน

ชุดภาพสำเร็จของสองระบบไม่เท่ากัน คะแนน success-only จึงมีทั้งความต่างของโมเดลและความต่างของประชากรปะปนกัน STRICT_COMPLETE ทำให้รายงานหลักเป็น N/A และคง failures ไว้ ไม่แทนด้วยศูนย์และไม่ทำให้ระบบหายจากตาราง ภาพที่ valid empty ยังต้องได้ execution success พร้อม FP/FN ตาม GT ไม่ใช่เปลี่ยนเป็น failure เพื่อเลี่ยงคะแนนต่ำ

## 6. สิ่งที่ยังบอกไม่ได้จากภาพและ aggregate

ยังไม่มี public same-frame mask case study ที่ตรวจสิทธิ์และจัดทำตามสองระบบ/เกณฑ์นี้ครบ จึงไม่อ้างว่าภาพใดพิสูจน์ความแนบของ mask, coverage superiority, near tie หรือ CCTV robustness รายงานการดู saved TRAIN overlays ก่อนรับ mapping เป็น bounded sanity check และไม่ใช่ validation accuracy selection หรือ independent human annotation-quality review

## 7. เมื่อต้องตัดสินใจ

ขณะนี้ยังไม่มีข้อมูลครบสำหรับเลือกระบบด้านคุณภาพ สิ่งที่ทราบคือ configurations เดิมมี execution limitations ขั้นถัดไปควรเสนอ resource revision ที่พิสูจน์บน TRAIN และกำหนดกติกาก่อนรอบใหม่ โดยไม่ tune จาก VAL หรือเริ่มทดลองต่อเอง

[Technical report](REPORT.md) · [ข้อจำกัดข้อมูล](DATASET_DETAILS.md) · [รายการ failures]({metric}/FAILURES.csv) · [หลักฐาน run](cohorts/first_cpi_t3b/RUN_MANIFEST.json)
''')
    text('DATA_SCHEMA.md',f'''# Public Data Schema — First CPI T3b Cohort

UTF-8 CSV with one header; JSON null and empty CSV metric cells mean unavailable, never fabricated zero. This publication schema documents existing fields and adds navigation; it does not change source result files. [Historical schema](reports/archive/pre_public_snapshot/DATA_SCHEMA.md) is preserved.

## QUALITY_RESULTS.csv

Key: `(system_id,population,matching_view)`; 8 unique rows. `system_id` names a configured parser system, `population=main|reference`, `matching_view=primary|secondary`, `IoU_threshold=0.50|0.75` (bbox, fraction). `status=INCOMPLETE`, `main_score_eligible=False` in every current row.

`frames`: fixed image denominator. `G_loc`: eligible GT localization persons; `G_sem`: eligible semantic persons, subset of G_loc. `frames_complete`, `frames_failed`, `frames_invalid`, `frames_not_attempted` sum to `frames`. Completion is assessed separately per system and population; two matching views do not duplicate inference.

Main metric columns are `Q_person_sem_GT,TP,FP,FN,localization_recall,localization_precision`; all blank for current INCOMPLETE rows. For an eligible complete population, TP/FP/FN are one-to-one final bbox matches/unmatched persons; recall=TP/G_loc and precision=TP/(TP+FP), undefined when the denominator is zero. Counts are integers; ratios are fractions 0–1. FP is unmatched relative to released annotations, not proof that a physical person does not exist.

## Person semantic metric

For each semantically eligible matched GT person, the accepted GT-derived domain supplies a confusion matrix with an extra UNMAPPED-prediction error column. For each foreground class with GT support, IoU=TP/(GT support+prediction support−TP). The person's IoU is the mean over its fixed GT-supported foreground classes. `Q_person_sem_GT = sum(matched eligible GT person IoUs) / G_sem`; unmatched G_sem persons contribute zero. Undefined absent-GT support remains null. It is not pooled global mIoU or official AP. See [actual evaluator](src/application_v2/evaluation.py), [score boundary](src/application_v2/scoring.py) and [aggregation](src/application_v2/comparison.py).

## OPERATIONAL_SUCCESS_ONLY_DIAGNOSTICS.csv

Same system/population/view keys. `label=SUCCESS_ONLY_DIAGNOSTIC_NOT_MAIN_SCORE`, `scored_frames`, observed `G_loc/G_sem`, conditional Q and TP/FP/FN describe only successfully scored frames. Different successful populations prohibit treating these as main scores or ranking systems. Undefined values stay blank/null.

## FAILURES.csv

One unique `(component,image_id)` per native failure/invalid event; 566 rows. Fields: `component,image_id,status,failure_stage,failure_kind,error_last_line,retries,source_ledger`. `failure_kind=CUDA_OOM|UNRESOLVED_INTERRUPTION`, `retries=0`; source ledger paths identify external immutable originals. A failure event does not independently add FN again; no operational-empty fallback is the primary policy.

## Native prediction and context interfaces

Native per-person integer grids, boxes/scores, original W/H, source/crop transforms, checkpoint/source/adapter/config/input hashes and separate native/YOLO identities are specified by [contracts.py](src/application_v2/contracts.py) and frozen [V12]({config}). Categorical resizing is nearest-neighbor; metric truth is lossless, never a colored/JPEG overlay. Native identity unsupported→null; supported but no instance→0. Stage rates carry stage/unit/numerator/denominator and return null on zero denominator; routing skips differ from failures.

Mapping [V3]({mapping}) keeps GT VOID outside the shared denominator, while unmapped predictions cannot create favorable GT void. Global known-target/owner-unknown pixels and per-person void are distinct. Background0, ignore/void and unsupported concepts must not collapse. Numeric source IDs are taxonomy-specific.

## Inventory and provenance

[MODEL_INVENTORY.csv](inventory/MODEL_INVENTORY.csv) is not a leaderboard. Download status, local file integrity, architecture load, bounded native inference, historical pilot, canonical export, use restriction and full-cohort completion are independent fields. Local SHA256 identifies local bytes; publisher authenticity is NOT independently verified without an upstream digest. Source hashes and config freezes predate public Git; Git commit/tag is publication provenance only.

Detailed GT/person bindings, 10,000 primary and secondary frame score journals, arrays and ledgers are external. Their absence in a clone must not be replaced with invented values. [ARTIFACTS.md](ARTIFACTS.md) describes access.
''')
    text('AGENTS.md',f'''# Agent continuation contract

Read README.md, STUDY_STATE.json, HANDOFF.md, EXPERIMENT_PROTOCOL.md and publication/PUBLICATION_STATE.json first. This directory is a **public staging snapshot** of the separate canonical working copy `{S.name}`; do not confuse them or auto-sync in either direction.

- The executed cohort is closed: FINISHED_WITH_INCOMPLETE_SYSTEMS. No new inference, retries, downloads, training, validation tuning, CCTV, hybrid, attribute study or benchmark is authorized by this repository.
- Preserve original results, null main metrics, failures, frozen config/decisions/mapping and historical reports. Do not promote CPI mapping to DIRECT_VERIFIED or use successful subsets to rank systems.
- Existing V11/V12 `full_benchmark: true` documents past scoped user approval, not permission for another run. Inventory download approvals were not benchmark approval for all variants.
- Use SETUP.md portable CPU checks first. Project-bound tests require separately supplied external assets; do not fabricate hash-bound fixtures or downgrade their gates to make a clone pass.
- Never install into the working YOLO environment, alter datasets/weights/remotes, execute old orchestrators, blindly add artifacts or create/publish a remote without authorization.
- Preserve research scope: independent noncommercial academic evaluation; Sapiens2 use restrictions are independent from historical technical runs; 5B remains excluded. No commercial/deployment permission is claimed.
- Prefer pathlib/root-relative paths. Original absolute paths in historical records are provenance, not public download URLs.
- Source changes must be reviewed/tested locally, then explicitly cherry-picked/synced to the canonical working copy by path/hash manifest. Never overwrite either working tree wholesale. Capture new source hashes and require a newly approved configuration for a new experiment.
- Current active docs, historical reports and external dependency references are indexed separately. A post-run Git commit is not the launch revision. Never force push, rewrite tags or publish old Git histories automatically.

Safe entry points: `python scripts/validate_public_repository.py` (stdlib checks) and `python scripts/run_portable_cpu_tests.py` (synthetic CPU suite only). Neither loads models or opens original datasets. Full reproduction limits are in REPRODUCIBILITY.md.
''')
    text('HANDOFF.md',f'''# Handoff — Closed First CPI Cohort

## Current result

Two CPI CIHP native parsers plus frozen YOLO26x ran T3b FP32 over one 5,000-image reference input population; 4,961-image main is a scoring membership subset. Both systems are INCOMPLETE under STRICT_COMPLETE. Main metrics are null. Keep all 8 rows and 566 native failure/invalid records. [Report](REPORT.md), [run manifest](cohorts/first_cpi_t3b/RUN_MANIFEST.json).

## Authority and state

Current executed config [{config}]({config}) / decision [{decision}]({decision}); original [{R}/FREEZE.json]({R}/FREEZE.json) and restored [{R}/RESTORED_PROFILE_FREEZE.json]({R}/RESTORED_PROFILE_FREEZE.json). Source hashes, actual environment strings and scope take precedence over a latest-number filename or stale prose. Mapping remains ACCEPTED_WITH_INDIRECT_EVIDENCE. The full roster/inventory is separate.

## First actions for another person/agent

1. Run the stdlib public validator; inspect STUDY_STATE.json and the canonical CSVs.
2. Follow SETUP.md for tested portable CPU fixtures. Do not execute first_cohort_entrypoint/restore/native workers as setup.
3. Read the explicit external artifact inventory. No public dataset/weight/prediction mirror exists; request authorized local access or independently acquire matching upstream bytes subject to terms.
4. Read reports/HISTORY_INDEX.md to separate superseded Stage 0 proposals from accepted cohort policies and terminal execution evidence.

## Outstanding work

The experiments did not establish a quality winner. OOM correction and interrupted-image handling in any future run need a new, reviewable execution revision, with TRAIN-only engineering and frozen population/scoring rules before any new VAL pass. Do not retroactively retry or fill the present main scores. No need to reopen the accepted five policies or the closed channel-header search absent concrete new contradictions.

Clean cloning does not provide native CUDA builds, all annotation bindings or semantic visual case assets. Public image redistribution is not cleared. Licensing remains component-specific; deployment is outside research scope. Repository publication is pending the single public-approval gate; an agent outside the account has not been tested.

## Working-copy synchronization

Canonical editable research remains the sibling `{S.name}` (not Git-initialized at snapshot). This candidate is `{P.name}`. Source copies preserve bytes and original hashes in publication/SOURCE_COPY_MANIFEST.json. No files are moved/deleted. Changes in this staging copy do not automatically reach the canonical study; review explicit diffs and before/after hashes before a future authorized sync.
''')
    text('SETUP.md',f'''# Setup and Safe Checks

## Portable CPU checks

Use Python 3.10+ (tested interpreter is recorded in publication validation). Create a fresh environment outside datasets/model trees if needed; installation is optional and subject to your environment policy:

```bash
python3 -m venv ../human-parsing-cpu
../human-parsing-cpu/bin/python -m pip install -r requirements-cpu.txt
../human-parsing-cpu/bin/python scripts/validate_public_repository.py
../human-parsing-cpu/bin/python scripts/run_portable_cpu_tests.py
```

No installation was performed merely for publication. The clean-checkout test uses the already available, compatible audit Python. The portable runner explicitly selects synthetic/config CPU modules that require no datasets/weights. Other retained tests are project-bound, not silently skipped as passing. Historical validation-package tests require external detailed GT bindings and their exact hashes. [Validation evidence](publication/CLEAN_CHECKOUT_VALIDATION.json) gives actual counts/versions; old server **151 tests** are separate evidence, not the clean-checkout count.

## Native execution environment (historical, not install/run authorization)

The executed native CPI worker used isolated parser-legacy-cu113; YOLO used the existing YOLO environment; CPU scoring used mhpv2-stage0. See [environment table](env_specs/EXECUTED_ENVIRONMENTS.csv) for actual Python/Torch/CUDA/GPU strings extracted from run manifests, and [CPU pins](requirements-cpu.txt). Do not install old MMDetection/MMCV/CUDA dependencies into the YOLO environment or change driver/system CUDA.

Third-party code, extensions, checkpoint bytes, dataset archives, detailed GT packages and native output arrays are absent from Git. Versions alone are not a complete native dependency lock. Historic environment freezes/source/config hashes are retained where available; no fresh native compatibility claim is made here. Source repositories/revisions and required patches are in THIRD_PARTY_NOTICES.md and ARTIFACTS.md.

## Executed artifacts

Place authorized external resources at the workspace-relative locations referenced by the unchanged frozen config, or propose a separately validated relocation/config revision. Never silently change path-bearing historical records or hash-bound configs. No single clone-and-run command can reproduce the full benchmark from this repository alone.
''')
    text('requirements-cpu.txt',(S/'env_specs/mhpv2-stage0.txt').read_text())
    text('REPRODUCIBILITY.md',f'''# Reproducibility Boundaries

## What can be verified without account access or GPU

The released summary CSVs/JSON reports, population totals, INCOMPLETE/null policy, failure inventory, source/config copy hashes, synthetic matching/scoring/lifecycle contracts and documentation navigation can be checked on CPU using SETUP.md. The public validator does not infer missing measurements or start subprocess model workers.

## What remains external

Datasets/checkpoints, detailed GT pixel/person bindings, native framework source/builds, 5,000-row source component ledgers, lossless per-image masks/boxes, packet arrays and both 10,000-row scoring journals remain local. Their original paths, sizes/hashes where recorded, source URLs and access status are in ARTIFACTS.md / publication/EXTERNAL_ARTIFACTS.json. No artifact is claimed publicly hosted when it is not. Native parser source/revision is separate from the later first-party Git snapshot.

The server post-export validator checked source journals/reports, original protected files and six YOLO Git statuses. A clean public clone can check the published summary counterparts and recorded hashes but cannot independently re-open omitted arrays. Per-target final scores are not fabricated from aggregate CSVs. Existing generation scripts may require server-only files or refuse overwriting; they are historical implementation, not quickstart commands.

## Provenance distinctions

- Launch freeze V11 and restored V12 establish executed configuration; no Git commit existed for the study at launch.
- The first public candidate commit is an explicitly post-run snapshot. It must not be cited as the launch commit or proof of pre-registration.
- Local checkpoint SHA256 proves identity with the locally inventoried bytes; without an upstream published digest it is not cryptographic author-authenticity verification.
- Archived 151 application tests and original 67 foundation evidence are not collapsed into a new 218-test claim. Clean-checkout portable counts are recorded separately.
- Scoped continuation of never-attempted CPI images and isolated detector restoration preserve the original trial/failure evidence; neither proves general cached scoring/resume.
- Historical reports retain their original knowledge/authorization scope. Current indexes do not rewrite them.

See [publication validation](publication/CLEAN_CHECKOUT_VALIDATION.json), [source copies](publication/SOURCE_COPY_MANIFEST.json), [run provenance](cohorts/first_cpi_t3b/RUN_MANIFEST.json), [component notices](THIRD_PARTY_NOTICES.md). No GPU benchmark was rerun for publication.
''')
    text('ARTIFACTS.md',f'''# External Artifacts and Access

Git contains first-party code/tests, exact frozen configs/decisions/mappings, reports, machine-readable summary results, small factual manifests and publication-generated plots. It contains no dataset RGB/GT pixels, weights, environment binaries, bulk predictions/logits or company CCTV. Source dataset photos/overlays are withheld because public redistribution rights have not been established for the selected images. No broad image/CSV/JSON ignore pattern hides essential summaries.

| External artifact | Recorded bytes | SHA256 / access |
|---|---:|---|
| datasets/CCIHP_icip.zip | 842,868,844 | 373f3183bf58c3e5637ba3564c9b8abef923dc434b78f469b3722282d1514829; user-transferred, no public mirror created |
| datasets/cihp-DatasetNinja.tar | 2,015,375,360 | 085d2b694a8c4e0081292a905972e1f31af9d454c12698427b187c7af67a2793; source project [DatasetNinja CIHP](https://datasetninja.com/cihp) |
| datasets/LV-MHP-v2.zip | See original import | 89f010742d4797d3efd7a7eab83a405d9828749381da20638a03df947238059e; [original MHP project](https://lv-mhp.github.io/) |
| models/yolo26x-seg.pt | See source checkpoint provenance | 92b3de0065766a17180d6219858717dc9d03cdce8a3ca9576c97fd75aabb64f3; frozen upstream dependency |
| CPI_R50_CIHP / CPI_ConvNeXtB_CIHP | 571,901,148 / 1,301,413,296 | Hashes, official source URLs and license notes in [inventory](inventory/MODEL_INVENTORY.csv) |
| GT context bindings, component ledgers, per-image arrays, scoring journals | Per-item metadata where available | [External manifest](publication/EXTERNAL_ARTIFACTS.json); local custodian access only, no signed/restricted URL exposed |

Public upstream source links are not a promise that weights/datasets are currently anonymously downloadable. Exact acquisition must respect current source terms and applicable user authorization. Dataset rights, annotation rights, code, checkpoints and dependencies remain separate. No new acquisition was performed for this publication.

## Reconstructing a full local view

Obtain permitted matching external assets, verify their sizes and recorded hashes, preserve original read-only datasets, and recreate required native environments from inspected version/source records. Restore detailed GT packages and original run-owned outputs at their recorded relative paths before running project-bound validators. Unknown or unavailable assets remain unavailable; do not substitute approximate GT, default checkpoints or guessed channel mappings. A new model execution still requires approval.

The working copy remains `{S.name}` next to this public staging copy. Local paths in retained evidence describe that workspace, not Internet endpoints. Some older records reference pilot experiments outside this repository; those dependencies are not automatically redistributed or declared reproducible from a clone.
''')
    text('THIRD_PARTY_NOTICES.md','''# Third-Party and Redistribution Notes

This repository publishes a post-run research snapshot, not a bundle of pretrained models or datasets. No blanket third-party rights are inferred from public download access. The prior component-specific research-scope assessment is retained in provenance/LICENSE_MATRIX_DECISION5A_V1.csv and reports/LICENSE_ELIGIBILITY_REASSESSMENT.md; those dated findings are not renewed commercial permission.

- CPI-Parser: official HAG-uestc/CPI-Parser, source d62cae523ba913fec4a7fda5816bc1d96bbf644d, Apache-2.0. Preserved config excerpts/resolved configuration metadata in run evidence retain applicable Apache terms; see licenses/CPI-Parser-Apache-2.0.txt. Native source tree/weights are external. No third-party parser source patch is silently applied by publication.
- M2FP, FASHN, D2FP, SCHP, QANet, RP-R-CNN and CDGNet: source/weights/dependency conditions are independent. Inventory and factual evidence do not redistribute their native code or checkpoints or grant permissions absent upstream terms. Historical native technical passes do not override usage restrictions.
- Sapiens2: historical files/technical pilot status remain distinguishable from current USE_RESTRICTED_SURVEILLANCE_RESEARCH; no new permission is asserted. 5B is excluded for resources. No Sapiens checkpoint/source distribution or execution is performed.
- Native MHP evaluator compatibility is first-party wrapper code referencing an external MIT implementation/revision; original evaluator sources are not vendored here. It was not the official metric used by the current custom CCIHP cohort.
- NumPy, SciPy, Pillow and PyYAML are dependencies installed separately under their own licenses. No environment/package binary is shipped. YOLO/Ultralytics remains an external frozen dependency under its own terms, not relicensed here.
- CIHP image rights, CCIHP annotation rights and DatasetNinja conversion terms are separate. No RGB/GT pixel examples are redistributed. The completion plot is generated solely from this study's execution counts.

First-party source licensing has not been newly selected by this preparation task. Public readability/publication approval must not be presented as an unrestricted commercial software license. See LICENSE.md.
''')
    text('LICENSE.md','''# Rights and License Status

No new blanket license for first-party study code/documentation has been selected in this publication-preparation task. Copyright and applicable rights remain with their respective owners. This notice does not grant rights to datasets, photographs, pretrained weights or third-party software. Public GitHub publication and an open-source license grant are different decisions.

Preserved CPI configuration excerpts/metadata remain subject to their original Apache-2.0 terms and attribution in THIRD_PARTY_NOTICES.md / licenses/CPI-Parser-Apache-2.0.txt. External components retain their own licenses. This repository does not claim commercial or deployment clearance.
''')
    text('.gitignore','''# External assets and runtime output only; do not ignore all JSON/CSV/images.
/.venv/
/.venvs/
/parser_envs/
/datasets/
/models/
/third_party/
/predictions/
/outputs/
/logs/
__pycache__/
*.py[cod]
.pytest_cache/
.DS_Store
.env
.env.*
*.pem
*.key
*.pth
*.pt
*.safetensors
*.npz
*.npy
''')
    # Machine-readable current state is explicitly publication metadata, not a rewritten historical config.
    js('STUDY_STATE.json',dict(schema_version='public-1.0',study_id='human_parsing_mhpv2',display_name='Human Parsing Study',
       current_run_id=RUN,benchmark_status=final['status'],stage='FIRST_COHORT_EXECUTION_FINISHED',
       current_config=config,current_decision=decision,current_mapping=mapping,semantic_mapping_evidence='ACCEPTED_WITH_INDIRECT_EVIDENCE',
       populations=dict(main=dict(images=4961,G_loc=17434,G_sem=17390),reference=dict(images=5000,G_loc=17548,G_sem=17504)),
       primary_reporting_policy='STRICT_COMPLETE',main_score_eligible=False,matching_primary=.5,matching_secondary=.75,
       quality_only=True,new_experiment_authorized=False,publication_status='PENDING_PUBLIC_APPROVAL',public_url=None,
       historical_stage0_full_roster_status='BLOCKED_NOT_THE_CURRENT_COHORT_STATUS',
       authoritative_result_csv=f'{metric}/QUALITY_RESULTS.csv',run_manifest='cohorts/first_cpi_t3b/RUN_MANIFEST.json',
       original_study_state_archive='reports/archive/pre_public_snapshot/STUDY_STATE.json'))
    js('cohorts/first_cpi_t3b/RUN_MANIFEST.json',dict(run_id=RUN,status=final['status'],config=config,decision=decision,
       original_launch_freeze=f'{R}/FREEZE.json',restored_profile_freeze=f'{R}/RESTORED_PROFILE_FREEZE.json',
       final_validation=f'{R}/FINAL_BENCHMARK_VALIDATION.json',post_export_verification=f'{R}/POST_EXPORT_VERIFICATION.json',
       metrics_directory=metric,systems=['CPI_R50_CIHP','CPI_ConvNeXtB_CIHP'],dependency='YOLO26X_FROZEN',track='T3B',precision='FP32',
       source_commit_at_launch=None,source_commit_at_launch_reason='STUDY_NOT_GIT_INITIALIZED_AT_LAUNCH',
       public_git_snapshot_role='POST_RUN_NOT_LAUNCH_REVISION',full_reproduction_from_clone=False,new_execution_authorized=False))
    js('cohorts/first_cpi_t3b/POPULATIONS.json',dict(source='Unchanged accepted config and source report totals',
       main=dict(images=4961,G_loc=17434,G_sem=17390,role='EXACT_SOURCE_OVERLAP_CONTROLLED'),
       reference=dict(images=5000,G_loc=17548,G_sem=17504,role='ORIGINAL_RELEASED_VALIDATION'),
       excluded_from_main=39,inference_populations=1,scoring_populations=2,posthoc_exclusions=False,
       full_person_GT_bindings='EXTERNAL_NOT_REDISTRIBUTED',membership_authority=config))
    # Normalize the old broad inventory without claiming fresh inference or final benchmark readiness.
    original=list(csv.DictReader((S/'provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv').open()))
    rows=[]
    for x in original:
        path=x.get('checkpoint_path',''); downloaded=bool(path and (S.parent/path).is_file())
        loaded=x.get('checkpoint_loaded')=='True'
        rows.append(dict(model_id=x['model_id'],family=x['family'],variant=x['model_id'],backbone=x.get('backbone',''),
          training_dataset=x.get('training_dataset','UNKNOWN'),native_classes_including_background=x.get('native_class_count',''),
          native_mode=x.get('mode','UNKNOWN'),component_only=x.get('component_only','False'),framework=x.get('framework','UNKNOWN'),
          official_repository=x.get('official_repository',''),source_commit=x.get('source_commit',''),official_checkpoint_url=x.get('official_checkpoint_url',''),
          original_filename=x.get('original_filename','NOT_VERIFIED'),local_filename=Path(path).name if path else '',
          checkpoint_workspace_relative=path,bytes=x.get('checkpoint_bytes',''),local_sha256=x.get('checkpoint_sha256',''),
          download_status='DOWNLOADED' if downloaded else 'NOT_VERIFIED_LOCAL',
          integrity_status='LOCAL_SHA256_RECORDED' if x.get('checkpoint_sha256') else 'NOT_VERIFIED',
          publisher_authenticity='NOT_INDEPENDENTLY_VERIFIED_BY_UPSTREAM_DIGEST',
          checkpoint_load_status='LOADED' if loaded else 'NOT_TESTED',
          bounded_inference_status='INFERENCE_PASS' if x.get('status')=='BOUNDED_NATIVE_PASS' else 'NOT_TESTED',
          canonical_export=x.get('canonical_contract','NOT_TESTED'),historical_pilot_status=x.get('historical_pilot_status','NOT_TESTED'),
          current_use_eligibility=x.get('use_eligibility','UNKNOWN'),license_notes=x.get('code_weight_dependency_licenses',''),
          T4_FP32_feasibility='BOUNDED_PASS_NOT_FULL_POPULATION_CERTIFICATION' if x.get('status')=='BOUNDED_NATIVE_PASS' else 'NOT_TESTED_OR_RESTRICTED',
          first_cohort_status='INCOMPLETE' if x['model_id'] in ['CPI_R50_CIHP','CPI_ConvNeXtB_CIHP'] else 'NOT_IN_APPROVED_BENCHMARK',
          evidence=x.get('run_manifest','') or x.get('evidence',''),notes=x.get('reason','') or x.get('technical_status_note','')))
    path=P/'inventory/MODEL_INVENTORY.csv';path.parent.mkdir(exist_ok=True)
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");writer.writeheader();writer.writerows(rows)
    text('inventory/README.md','''# Model Inventory (not benchmark results)

MODEL_INVENTORY.csv derives from the unchanged dated HANDOFF_V6 registry and existing local checkpoint presence. It contains 29 variant/component/watchlist records, not 29 benchmarked systems. It does not turn 21 bounded native passes or 8 CPI route packets into 21/8 scientifically accepted comparison systems.

DOWNLOADED, LOCAL_SHA256_RECORDED, LOADED, INFERENCE_PASS, NOT_TESTED, canonical export and USE_RESTRICTED are separate dimensions. Original filenames may remain NOT_VERIFIED_LEGACY_RENAMED_FILE. A local hash is a fingerprint, not author-authenticity proof. Bounded-pass resource values are not a timing/VRAM leaderboard. All non-first-cohort variants remain NOT_IN_APPROVED_BENCHMARK. Historical Sapiens technical evidence does not clear current intended-use restrictions; CDGNet tensor inspection is not model inference.

The source registry is retained byte-identically in provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv. Full checkpoint files remain external. No files were downloaded or models executed for this table.
''')
    # Exact executed package/runtime strings, not freshly measured deployment performance.
    native_paths=['execution/CPI_R50_CIHP/RUN.json','continuation_20261019/CPI_ConvNeXtB_CIHP_COMBINED/RUN.json','execution_restored_detector_v1/YOLO26X_FROZEN/RUN.json']
    env=[]
    for n in native_paths:
        x=json.loads((S/R/n).read_text());env.append({k:x.get(k) for k in ['model_id','python','torch','cuda_runtime','GPU','precision','autocast','TF32']})
    with (P/'env_specs/EXECUTED_ENVIRONMENTS.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(env[0]),lineterminator="\n");writer.writeheader();writer.writerows(env)
    # History is an index, not a rewrite or blanket claim all linked external evidence is in Git.
    history=[]
    for p in sorted((S/'reports').glob('*.md')):
        if 'ppss' in p.name.lower():continue
        public=P/'reports'/p.name
        history.append(dict(path=str(p.relative_to(S)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
          public_copy=public.exists(),role='TERMINAL_EXECUTION_REPORT' if p.name.startswith('FIRST_COHORT_T3B_BENCHMARK_REPORT') else 'HISTORICAL_CONTEXT_NOT_CURRENT_AUTHORIZATION'))
    js('publication/HISTORY_INDEX.json',dict(current_documents=['README.md','STUDY_STANDARD.md','EXPERIMENT_PROTOCOL.md','DATASET_DETAILS.md','REPORT.md','DATA_SCHEMA.md','HANDOFF.md'],
       current_config=config,current_decision=decision,history=history,
       original_reports_unchanged=True,external_link_policy='Historical references may require local artifacts; do not treat unavailable evidence as reproduced'))
    lines=['# Historical Evidence Index','','Current authority: [EXPERIMENT_PROTOCOL.md](../EXPERIMENT_PROTOCOL.md), [STUDY_STATE.json](../STUDY_STATE.json), [terminal report](../REPORT.md). Older Stage 0 reports may say benchmark unauthorized or checkpoints unavailable; those were dated facts, not current authority. No historical text is rewritten to anticipate later outcomes.','','[Machine index](../publication/HISTORY_INDEX.json) contains hashes and publication status. Historical deep links may reference external artifacts; use ARTIFACTS.md. Original pre-public landing/schema/standard/state documents are preserved under archive/pre_public_snapshot/.','','| Report | Role |','|---|---|']
    lines += [f"| [{Path(x['path']).name}]({Path(x['path']).name}) | {x['role']} |" for x in history if x['public_copy']]
    text('reports/HISTORY_INDEX.md','\n'.join(lines))
    print(json.dumps(dict(documents_written=True,inventory_records=len(rows),new_inference=False,remote_created=False)))


if __name__=='__main__':main()
