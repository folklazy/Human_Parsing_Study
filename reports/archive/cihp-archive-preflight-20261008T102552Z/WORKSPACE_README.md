# Human Body Extraction

## Human Parsing dataset reassessment — 2026-10-08

[Current reassessment](Human_Parsing_MHPv2_Study/reports/DATASET_REASSESSMENT.md) prepares approved MHP-v2 readable views (train 15,400; validation 4,999; exact-train-overlap-controlled validation 4,347), 30 random TRAIN GT diagnostics and a separately pinned evaluator wrapper. 51 bounded tests passed; no parser/checkpoint inference or full benchmark ran. CIHP is absent locally: its official archive metadata is 2,033,753,964 bytes; acquisition/quality/license review awaits approval. CIHP candidate-primary and MHP-v2 provisional-secondary roles are not frozen. PPSS remains paused; previous YOLO assets are unchanged. See the [study landing page](Human_Parsing_MHPv2_Study/README.md). Earlier sections below are historical and do not override the current review gate; the newly transferred ZIP now exists and matches its earlier recorded hash.

## Human Parsing MHP-v2 Stage 0 — 2026-10-08

The [Stage 0A–0D audit](Human_Parsing_MHPv2_Study/reports/STAGE0_FEASIBILITY_REPORT.md) is **BLOCKED, waiting for review**. All 25,403 images were inventoried and 54,316 native person planes verified; four required RGB inputs fail decoding. Contracts and synthetic evaluator tests were executed, but model weights were deferred and no actual parser inference ran. PPSS is paused. Previous YOLO results/environments remain unchanged. See the [study landing page](Human_Parsing_MHPv2_Study/README.md) for current evidence; sections below describe earlier work.

## PPSS external-dataset audit — 2026-10-08

The [Human Parsing study](Human_Parsing_MHPv2_Study/README.md) contains a read-only
[PPSS audit](Human_Parsing_MHPv2_Study/reports/PPSS_DATASET_AUDIT.md): 3,961 image/GT
pairs correspond to the current official download index, with warnings about the
paper's 3,673 count, a cross-split duplicate and completion-like GT. MHP-v2 remains
the primary proposed benchmark. PPSS supplies pedestrian crops, not full frames;
no parser inference or benchmark was started. The broader Human Parsing Stage 0
has not yet been executed; this audit stops at review.

## Shared dataset import — 2026-10-07

[LV-MHP-v2](datasets/LV-MHP-v2/README.txt) is available at `datasets/LV-MHP-v2/`,
with its original train (15,403 images), val (5,000 images), and test (5,000 images)
splits. Train and val include per-person parsing and pose annotations; the supplied
test split contains images without parsing annotations. The historical import recorded the source ZIP; it is no longer present locally at the Stage 0 audit.
All 179,896 archive entries passed CRC checks, and image lists match the extracted
images. See [import validation](datasets/LV-MHP-v2/IMPORT_VALIDATION.json).
The [import script](scripts/import_lv_mhp_v2.py) handles this archive's wrapped
32-bit offsets in memory without changing the ZIP. No model experiment was started.

## Master synthesis complete — 2026-10-06

The [17-model Master study](YOLO_Instance_Segmentation_MOTS20_Scaling_Study/README.md) is COMPLETE / PASS WITH WARNINGS. It merges all five completed canonical tiers, with no inference or benchmark rerun. Read [MASTER_RESULTS.md](YOLO_Instance_Segmentation_MOTS20_Scaling_Study/MASTER_RESULTS.md) for scaling, Pareto fronts and conditional robustness candidates. No further experiment is started.

## Documentation design — 2026-10-02

The scaling study separates compact quantitative RESULTS_SUMMARY_TH from visual/qualitative
PRESENTATION_SUMMARY_TH. All five tiers each include four actual
same-frame MOTS20 cases reconstructed from saved predictions. Small and Nano use the shared visual presentation format.
This documentation update reran no inference and changed no benchmark values.

## Study setup — 2026-10-02

All six scaling-study repositories are now present as separate workspace siblings. Largest and Second-largest expose canonical CSVs and four standardized report levels; their historical PASS WITH WARNINGS is retained. Medium is now COMPLETE / PASS WITH WARNINGS (canonical run benchmark-20261002T075505Z); Small is COMPLETE / PASS WITH WARNINGS (canonical run benchmark-20261005T051531Z); Nano is COMPLETE / PASS WITH WARNINGS (canonical run benchmark-20261005T083307Z). No inference, checkpoint downloads or final synthesis occurred during Stage 0.

- [Largest (X/E)](YOLO_Large_Seg_MOTS20_Benchmark/README.md)
- [Second-largest (L/C)](YOLO_Second_Largest_Seg_MOTS20_Benchmark/README.md)
- [Medium (M)](YOLO_Medium_Seg_MOTS20_Benchmark/README.md)
- [Small (S)](YOLO_Small_Seg_MOTS20_Benchmark/README.md)
- [Nano (N)](YOLO_Nano_Seg_MOTS20_Benchmark/README.md)
- [Master Study](YOLO_Instance_Segmentation_MOTS20_Scaling_Study/README.md)

Read [YOLO_Instance_Segmentation_MOTS20_Scaling_Study/STUDY_STANDARD.md](YOLO_Instance_Segmentation_MOTS20_Scaling_Study/STUDY_STANDARD.md) before any future tier. Shared datasets, models and `.venv/` remain at workspace root; invoke `.venv/bin/python` directly. Await explicit authorization before executing the next tier. Earlier dated status notes below are preserved.


## Current workspace status — 2026-10-01

- [YOLO_Second_Largest_Seg_MOTS20_Benchmark](YOLO_Second_Largest_Seg_MOTS20_Benchmark/README.md)
  is Experiment 2: the **second-largest available variant comparison**, using
  YOLO26l, YOLO11l, YOLOv8l and YOLOv9c segmentation checkpoints. Dataset hashes,
  ordering, dimensions, GT, metadata and the environment match Experiment 1.
  The same 100-frame preflight passed for all models; AP maxDet=200 exactly
  matched 1000 on all three AP metrics. Run `benchmark-20261001T0352Z` completed
  all four models × 2,862 frames and all 12 clean timing runs. YOLO26l has the
  highest mask mAP (0.586237), lowest mean pipeline latency (76.403 ms) and
  lowest peak allocated VRAM (777.52 MiB). YOLOv9c has the lowest mean neural
  inference latency (35.293 ms), just 0.094 ms below YOLO11l; do not overinterpret
  that small difference. See the experiment reports for cross-tier scaling and
  scientific limitations; these measurements do not establish CCTV suitability.
  Checkpoints remain shared under `models/`. Experiment 1 and the pilot are
  frozen references; no packages or datasets were changed.

- [YOLO_Large_Seg_MOTS20_Benchmark](YOLO_Large_Seg_MOTS20_Benchmark/README.md)
  is the separately authorized largest-variant benchmark: YOLO26x, YOLO11x,
  YOLOv8x and YOLOv9e segmentation, pretrained inference only. Its
  [protocol](YOLO_Large_Seg_MOTS20_Benchmark/EXPERIMENT_PROTOCOL.md) gates the
  2,862-frame accuracy run on a four-model 100-frame preflight. See its
  [main report](YOLO_Large_Seg_MOTS20_Benchmark/REPORT.md) for execution status
  and results. The validated pilot remains preserved.
  Completed run `benchmark-20260929T0520Z`: PASS WITH WARNINGS, all four models
  processed 2,862 frames, common AP maxDet=200, and 36 final consistency checks
  passed. YOLO26x had highest mask accuracy; YOLOv9e had fastest inference and
  lowest peak allocated VRAM. Clean repeated timing replaces a preserved initial
  pass flagged for non-idle GPU starts. This does not establish CCTV robustness.

- [Person_Segmentation_Pilot](Person_Segmentation_Pilot/README.md) is the active
  preliminary MOTS20 person-segmentation experiment. Its authorized smoke scope is
  MOTS20-02 frames 000001–000005 with `models/yolo11n-seg.pt`; full screening is not
  authorized within that pilot. The new benchmark has separate authorization.
  MOTS20 results do not establish final CCTV suitability.
  The five-frame pipeline has since been optimized with bit-identical predictions
  and unchanged metrics; see its
  [profiling and cap-validation report](Person_Segmentation_Pilot/metrics/optimization-report-20260924T082749882752Z/REPORT.md).
- Source/GT: `datasets/MOTS/MOTS/train/<sequence>/{img1,gt/gt.txt}`. The four train
  sequences contain 2,862 frames. `datasets/MOTS/MOTS/test` has no local GT.
  `datasets/MOTSLabels/MOTSLabels` duplicates the bundled GT and is not another
  evaluation source. All dataset files are preserved.
- OVIS images are at `datasets/OVIS/valid/valid`. `annotations_valid_withgt.json`
  contains GT; `annotations_valid.json` has null annotations. OVIS is outside the
  current pilot scope.
- Checkpoints remain at `models/yolo11n-seg.pt` and `models/yolo26s-seg.pt`.
  The benchmark additionally uses official `models/yolo26x-seg.pt`,
  `models/yolo11x-seg.pt`, `models/yolov8x-seg.pt`, `models/yolov9e-seg.pt`;
  provenance, sizes and SHA256 are in its checkpoint manifest.
- Invoke `.venv/bin/python` directly. Python 3.12.3, PyTorch 2.14.0+cu130,
  torchvision 0.29.0+cu130, Ultralytics 8.4.160, CUDA 13.0, Tesla T4.
  The user-authorized addition of `pycocotools==2.0.11` changed no other installed
  package versions; before/after records are under the pilot's `logs/setup-*`.
  `environments/yolo.freeze.txt` is the historical pre-installation snapshot.
- `Project_test0`, the old `dataset/`, and `datasets/Legacy_Images` were absent
  when this pilot began. `.venvs/` has not been created. No old files were removed
  or environments moved by the pilot.

The notes below are retained historical workspace documentation. Their old
inventory and commands referencing absent paths are not current run instructions;
use the linked pilot README above.

---

Workspace สำหรับการตรวจจับบุคคล, instance segmentation และการเปรียบเทียบโมเดล
บน Linux SSH GPU server ที่ใช้งานร่วมกัน

## โครงสร้างปัจจุบัน

```text
Human-Body-Extraction/
├── AGENTS.md                  # กฎถาวรสำหรับการทำงานใน workspace
├── README.md
├── .gitignore
├── environments/
│   ├── README.md
│   └── yolo.freeze.txt        # 60 packages ที่ติดตั้งใน environment เดิม
├── .venv/                    # environment เดิม เก็บไว้ไม่แก้ไข
├── dataset/                  # ภาพต้นฉบับ 7 ภาพ เก็บไว้ที่เดิม
├── datasets/
│   └── Legacy_Images -> ../dataset
├── models/
│   ├── yolo11n-seg.pt
│   └── yolo26s-seg.pt
├── Project_test0/
│   ├── infer.py
│   ├── inference.yaml.example
│   ├── requirements.txt
│   ├── README.md
│   ├── runs/
│   └── logs/                 # framework settings/cache
└── .workspace-backups/        # สำรองไฟล์ก่อน migration
```

Workspace ที่ตรวจพบอยู่ที่ `~/folk/Human-Body-Extraction` ไม่ได้ย้ายไปสร้างสำเนา
ที่ `~/Human-Body-Extraction` คำสั่งด้านล่างเริ่มจาก workspace root

## Experiment และทรัพยากรร่วม

- [Project_test0](Project_test0/README.md): YOLO instance-segmentation inference
  และการเปรียบเทียบ CPU/GPU พร้อมรายงาน JSON/CSV
- `models/yolo11n-seg.pt`: checkpoint ขนาดประมาณ 6.2 MB
- `models/yolo26s-seg.pt`: checkpoint ขนาดประมาณ 23.5 MB
- `datasets/Legacy_Images`: ภาพทดสอบ 7 ภาพจาก `dataset/` ผ่าน relative symlink
  ไม่มีการคัดลอก แก้ภาพ หรือสร้าง train/val/test split

Experiment ใหม่ต้องอยู่ใต้ workspace โดยตรง เช่น `YOLO26_MOTS20_Inference/`
ห้ามสร้างภายใน `Project_test0/` เก็บ source, configs, outputs, metrics, logs,
README และ requirements ของแต่ละ experiment ไว้ภายใน experiment นั้น
สร้างเฉพาะโฟลเดอร์ที่ใช้งานจริง อ่านกฎเต็มที่ [AGENTS.md](AGENTS.md)

## ใช้ environment เดิมในช่วงเปลี่ยนผ่าน

Environment เดิมใช้ Python 3.12.3, PyTorch 2.14.0+cu130, torchvision 0.29.0,
Ultralytics 8.4.160 และ PyYAML 6.0.3 การตรวจสอบพบ CUDA 13.0 และ Tesla T4

Activation script และ command launchers ของ `.venv` ยังอ้างถึงตำแหน่งเก่า
ให้เรียก interpreter โดยตรง ไม่ใช้ `source .venv/bin/activate`:

```bash
.venv/bin/python Project_test0/infer.py \
  ../datasets/Legacy_Images/thumb.jpg \
  --model ../models/yolo26s-seg.pt \
  --device 0 \
  --output "runs/example-$(date -u +%Y%m%dT%H%M%S%N)"
```

`source`, `model`, `output` แบบ relative อ้างอิงจาก `Project_test0/` เสมอ
ส่วน `--config` อ้างอิงจาก working directory ของผู้เรียก เช่น:

```bash
.venv/bin/python Project_test0/infer.py \
  --config Project_test0/inference.yaml.example \
  --output "runs/comparison-$(date -u +%Y%m%dT%H%M%S%N)"
```

ต้องใช้ checkpoint ที่มีอยู่ในเครื่อง และ output ต้องเป็นโฟลเดอร์ใหม่ภายใน
experiment หากไม่ระบุ `--output` จะใช้ `runs/segment` ซึ่งมีผลลัพธ์เดิมอยู่แล้ว
และจะถูกปฏิเสธเพื่อป้องกันการเขียนทับ ตัวอย่างจึงกำหนดชื่อ run ใหม่ทุกครั้ง

Framework settings และ matplotlib cache อยู่ใน `Project_test0/logs/`
เว้นแต่ผู้เรียกตั้งค่า `YOLO_CONFIG_DIR` หรือ `MPLCONFIGDIR` เอง

## Shared environments ในขั้นตอนถัดไป

ยังไม่ได้สร้าง `.venvs/yolo` หรือติดตั้งแพ็กเกจใหม่ ต้องได้รับอนุมัติให้สร้าง
environment ใหม่จาก snapshot แล้วตรวจ imports, CUDA, GPU และ inference ก่อน
ใช้คำสั่งนี้:

```bash
source .venvs/yolo/bin/activate
```

สร้าง `.venvs/sam3` เฉพาะเมื่อมีงาน SAM ที่ต้องใช้และตรวจแล้วว่า dependencies
ไม่สามารถใช้ environment เดิมร่วมกันได้ หลังสร้างและตรวจสอบแล้วจึงใช้:

```bash
source .venvs/sam3/bin/activate
```

ห้ามย้าย `.venv` ด้วย `mv` หรือปรับ dependencies จนกระทบ experiment เดิม
รายละเอียด snapshot อยู่ที่ [environments/README.md](environments/README.md)

## ผลลัพธ์และการสำรอง

ผลลัพธ์เดิมทั้งหมดอยู่ใน `Project_test0/runs/` การทดสอบ migration ใช้โฟลเดอร์
ใหม่ชื่อ `migration-...` แยกจากผลลัพธ์เดิม `.gitignore` ยกเว้นรายงาน
`comparison.csv`, `comparison.json`, `summary.json`, `report.json` ใน experiment
เดิมเพื่อให้เก็บใน Git ได้ และไม่ได้ ignore `metrics/` ของ experiment ใหม่

ไฟล์ต้นฉบับก่อน migration และ checksum ของข้อมูล โมเดล และผลลัพธ์เดิมอยู่ใน
`.workspace-backups/migration.ihictsdh/` ไม่มีการเริ่ม Git repository ใหม่
