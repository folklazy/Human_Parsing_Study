# Legacy references — reuse without moving or rerunning

## วิธีอ่านตำแหน่งและหลักฐาน

ตารางข้างล่างเป็น **local workspace-relative locations** ไม่ใช่ public download URLs Fingerprints ของไฟล์เล็กและบทบาทอยู่ใน [LEGACY_EVIDENCE.json](../manifests/LEGACY_EVIDENCE.json) SETUP ตรวจ existence/อ่าน evidence/บันทึก hashes ไม่ได้ verify dataset/checkpoint bytes ซ้ำหรือรับรองผล tests ทั้งหมดใหม่

Public snapshot ที่ตรวจได้ก่อน SETUP: [commit 0cf406f](https://github.com/folklazy/Human_Parsing_Study/tree/0cf406f300f92ec8bd8502bae4a750a73632709a) เป็น post-work snapshot ไม่ใช่ launch commit Newer preparation/source files บางส่วนมีเฉพาะใน working copy ให้ดู availability ตามตาราง ไม่สมมติว่า clone ได้ทุกอย่าง

| รายการ / ตำแหน่ง local | บทบาทและการ reuse | ข้อจำกัด |
|---|---|---|
| `YOLO_Instance_Segmentation_MOTS20_Scaling_Study/` | Phase 1 completed Master; read-only baseline provenance | ไม่แก้ repository, results หรือ Git history |
| `YOLO_Large_Seg_MOTS20_Benchmark/` | Largest tier reference: README/protocol, baseline measurements | ไม่เอา MOTS20 settings มา freeze parsing โดยอัตโนมัติ; untracked files เดิมคงไว้ |
| `Human_Parsing_MHPv2_Study/manifests/YOLO26X_SOURCE.json` | Frozen YOLO checkpoint identity และ recorded SHA256 | weights ไม่ถูกโหลด/rehash ใน SETUP; MHP-related fields ในบันทึกนี้เป็น historical context |
| `Human_Parsing_MHPv2_Study/provenance/CCIHP_STAGE0F_ACTIVE_RUN.json` และ run ที่ชี้ถึง | Dataset structural audit, class distributions, duplicate/ownership warnings, existing review sample | Structural PASS ไม่พิสูจน์ physical-person correctness; CCIHP-specific ไม่ใช่ original native CIHP GT |
| `Human_Parsing_MHPv2_Study/provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V7.csv` | Existing variant/checkpoint/source/environment evidence ของผู้สมัคร | Inventory ไม่ใช่ current roster/readiness; local file ไม่ได้ถูกรวมทั้งชุดใน publication นี้ |
| preparation run `experiment-preparation-20261020T064124828436Z/CHECKPOINT_VERIFICATION.json` ภายใต้ `Human_Parsing_MHPv2_Study/provenance/RUN_MANIFESTS/` | Existing checkpoint fingerprints/recorded validation | local fingerprint ไม่พิสูจน์ publisher authenticity; ไม่ rehash weights ใหม่ |
| `Human_Parsing_MHPv2_Study/src/application_v2/` และ `tests/` | Reusable contracts/scoring/association/lifecycle และ synthetic tests | ต้องตรวจกับ route/GT/targets ที่จะใช้ ไม่รันทดสอบซ้ำทั้งหมดเพื่อ SETUP; public 0cf มีเพียง reviewed snapshot |
| `Human_Parsing_MHPv2_Study/src/experiment_qanet_batch_v1.py` และ `scripts/experiment_qanet_validation_worker_v1.py` | Historical two-QANet implementation เป็น reference เฉพาะจุด | บังคับสองรุ่น/old populations, resolve study จาก file location; ไม่ใช่ general seven-candidate runner และห้ามย้าย/execute ใน SETUP |
| `Human_Parsing_CCIHP_10_Image_Pilot/` | Saved native pilot outputs และเว็บ review เดิม | Feasibility/diagnostic evidence ไม่ใช่ final quality/ranking; ไม่คัด raw images/checkpoints เข้า public |
| `Human_Parsing_MHPv2_Study/metrics/first-cohort-benchmark-20261016T094257313856Z/` | Historical CPI T3b results/failures; primary scores null, STRICT_COMPLETE | ไม่เปลี่ยน denom/retry/นำมาปะเป็นผล protocol ใหม่; [published CSV](https://github.com/folklazy/Human_Parsing_Study/blob/0cf406f300f92ec8bd8502bae4a750a73632709a/metrics/first-cohort-benchmark-20261016T094257313856Z/QUALITY_RESULTS.csv) |
| `Human_Parsing_MHPv2_Study/taxonomy/APPLICATION_BODY_CLOTHING_CPI_ACCEPTED_V3.json` | Accepted historical CPI mapping, confidence ACCEPTED_WITH_INDIRECT_EVIDENCE | ไม่เท่ากับ accepted mappings/targets ของทุก candidate ใหม่ |
| `Human_Parsing_MHPv2_Study/reports/PROJECT_ROADMAP_TH_20261020.md` | WIP starting evidence; original archived/hash recorded | ข้อเสนอหก work packages/selection ยังไม่ accepted; [published WIP](https://github.com/folklazy/Human_Parsing_Study/blob/0cf406f300f92ec8bd8502bae4a750a73632709a/reports/PROJECT_ROADMAP_TH_20261020.md) |
| `HUMAN_PARSING_EXPERIMENT_DESIGN_TH.md`, `CODEX_HUMAN_PARSING_EXPERIMENT_HANDOFF_TH.md` และ old roster/preparation pointers | Historical design/preparation context | ชื่อไฟล์/active pointer เก่าไม่ยืนยัน scope ใหม่; ไม่ต้องปิด draft เก่าทั้งหมดก่อน A |
| shared `datasets/`, `models/human_parsing/`, `third_party/human_parsing/`, `.venvs/` | Physical assets/environments เดิม ใช้ logical references | External to public Git; no moves/copies/download/install |

## Dataset identities ที่อ้างจาก existing evidence เท่านั้น

Existing CCIHP audit execution manifest บันทึก CCIHP archive SHA256 `373f3183bf58c3e5637ba3564c9b8abef923dc434b78f469b3722282d1514829` และ DatasetNinja TAR `085d2b694a8c4e0081292a905972e1f31af9d454c12698427b187c7af67a2793` ไม่ hash archives ใหม่และไม่แปลว่า GT semantics เท่ากัน

Frozen YOLO manifest บันทึก checkpoint `models/yolo26x-seg.pt`, SHA256 `92b3de0065766a17180d6219858717dc9d03cdce8a3ca9576c97fd75aabb64f3` ไม่เป็นการโหลด/ตรวจ weights ใหม่

## Git snapshots ที่ตรวจจริงใน SETUP

- `Human_Parsing_Study_Public`: branch `main`, HEAD `0cf406f300f92ec8bd8502bae4a750a73632709a`; working tree สะอาดก่อน SETUP
- `YOLO_Instance_Segmentation_MOTS20_Scaling_Study`: branch `main`, HEAD `5551593459646fe42494958192e5410805ab4b48`; มี untracked work เดิม; บันทึกสถานะและคงไว้
- `YOLO_Large_Seg_MOTS20_Benchmark`: branch `main`, HEAD `172e21b9f2996bae74fb591cfdd1740e6e92dd46`; มี untracked work เดิม; บันทึกสถานะและคงไว้

Public/source checkout แยกกัน Root และ legacy working study ไม่มี `.git` จึงใช้ small-file hashes และ existing run manifests อ้าง source identity แทนการแต่ง launch commit
