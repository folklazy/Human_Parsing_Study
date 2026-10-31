# CCTV Human Parsing Benchmark

ทดสอบ pretrained parsing 9 checkpoints เดิมกับ CCTV partial annotations โดยเก็บภาพและ artifacts ภายใน workspace เท่านั้น เริ่มอ่าน [PROTOCOL.md](PROTOCOL.md) → [STATUS.md](STATUS.md) → [ผลจริง](reports/RESULTS_TH.md)

นี่เป็น experiment แยกที่ workspace root ตาม AGENTS.md ใช้ shared code จาก `../Human_Parsing_Benchmark/src/`, weights `../models/`, environments `../.venvs/` และ dataset `../datasets/CCTV_100_Evaluation/` ไม่มีการย้ายหรือลบงานเดิม ไม่มี nested Git ข้อมูล CIHP/native/common results เดิมคงเดิม

ชุดนี้มี90ภาพจริง (48day/42night),127คนที่มีannotatedparts. รู้labelsเฉพาะบางคน/บางส่วน จึงไม่รายงานfull-image mIoU/FP/personF1หรือoveralldeploymentwinner. ใช้macrorecall4และcross-classconfusionบนknownannotationpixels. ชื่อโฟลเดอร์100ไม่ใช่จำนวนประชากรที่ยืนยัน

## คำสั่ง

ใช้ path ของ environment โดยตรง ห้าม resolve symlink ของ Python จนหลุด environment:

```bash
.venvs/sapiens2-pilot/bin/python CCTV_Human_Parsing_Benchmark/scripts/benchmark.py --config CCTV_Human_Parsing_Benchmark/outputs/cctv-partial-20261031T1800Z/CONFIG.json
```

คำสั่งข้างบนอัปเดตรายงานจากstateที่บันทึกไว้เท่านั้น ไม่เปิดinference. Live progressอ่าน `outputs/<run>/BATCH_STATUS.json`, `CURRENT_WORKER.json`, `<model>/STATE.json` และ log ชื่อmodel. Ctrl+Cของviewerไม่หยุดdetachedcontroller

การรันใช้ `--run` เฉพาะfreshfrozenrunที่อนุญาตแล้ว ไม่มีautomaticretry/resume; ถ้ามีpartial/failedattemptต้องreconcileก่อน ห้ามลบหรือทับไฟล์เดิม

## Git และ privacy

PUBLIC repoเดิม `folklazy/Human_Parsing_Study` เก็บเฉพาะcode/tests/protocol/aggregateaudit/status/reportที่ตรวจแล้ว. ห้ามsyncCCTVimages/filenames/annotations/metadata/personroles/masks/logsขึ้นpublicGit. Local `outputs/` เก็บprivateinputmanifest,fullnative integer masks,YOLOcache,geometry/ownership/confidences,hashes,scoreconfusion,ledger,environment/attemptfailures. ไม่มีinferenceเพื่อการสี/training/CCTVtrackingในรอบนี้

เกณฑ์ยกระดับสู่ full benchmark ที่เลือก configuration ได้: [FULL_BENCHMARK_ACCEPTANCE_TH.md](reports/FULL_BENCHMARK_ACCEPTANCE_TH.md). รอบปัจจุบันไม่สร้าง labels ที่ยังขาดขึ้นมาเอง

ดู progress จริงแบบ read-only:

```bash
python3 CCTV_Human_Parsing_Benchmark/scripts/progress.py --watch
```

กด Ctrl+C ปิดเฉพาะviewer ไม่หยุดcontroller. PID/สถานะล่าสุดอ่านจากprivateJSONจริง; publicGitเป็นsnapshotตอนsync ไม่ใช่liveสถานะ
