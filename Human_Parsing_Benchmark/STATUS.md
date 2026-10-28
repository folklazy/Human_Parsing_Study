# Human Parsing Benchmark — current status

Updated 2026-10-29T00:40:16.529470+07:00 Bangkok (UTC+07)

**CPI_R50_ROUND_INCOMPLETE / QUEUE_STOPPED**. ใช้ SHARED_GPU_QUALITY_ONLY ตามผู้ใช้อนุมัติแล้ว; โหลดและ TRAIN warmup ผ่าน แต่ VAL `0000018` เกิด CUDA OOM จึงหยุดตาม failure policy ไม่มี retry/fallback หรือ ConvNeXt-B

- Native CIHP VAL 5,000: complete **3**, failed **1**, invalid **0**, not-attempted **4,996**, missing successful IDs **4,997**, duplicate/orphan **0**
- **STRICT_COMPLETE: main metrics null** ไม่จัดอันดับจาก subset; setup PASS แยกจาก VAL failure และ historical EXTERNAL_GPU_BUSY
- QANet/M2FP/D2FP/RP-R-CNN ปิดรอบเดิมครบแล้ว ไม่มี inference ซ้ำ; current cohort4/6 closed
- Frozen scientific config/checkpoint/FP32/preprocessing/YOLO/GT/scorer เดิม; shared timing/resource diagnostics ไม่ใช้ speed/VRAM ranking
- Round `cpi-r50-shared-20261028T172951337299Z`; parent `cihp-native-six-20261028T034103254470Z`; launch commit `4c7248ff7166cfe81ec5fe1dfda8cfe77ffe776c`; controller162019/worker162023 exit แล้ว

[รายงานหลักสำหรับส่งตรวจต่อ](reports/CIHP_CONTROLLED_CONTINUATION.md) / [canonical completion](runs/cihp-native-six-20261028T034103254470Z/cpi-r50-shared-20261028T172951337299Z/COMPLETION.json) / [postflight evidence](runs/cihp-native-six-20261028T034103254470Z/cpi-r50-shared-20261028T172951337299Z/POSTFLIGHT_VERIFICATION.json) / [current cohort](manifests/CIHP_NATIVE_COHORT_INDEX.json)

อ่านสถานะ: `python3 Human_Parsing_Benchmark/scripts/cpi_r50_progress.py --json` (`STOPPED_INCOMPLETE`, `queue_stopped=true`) Logs/status: `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/rounds/cpi-r50-shared-20261028T172951337299Z/ROUND_STATUS.json`, `WORKER.log`, `CONTROLLER.log`

Next: ส่งรายงาน CPI R50 ให้ผู้ใช้ตรวจและรอขอบเขตถัดไป ไม่ restart/retry/เปลี่ยน scientific protocol/เริ่ม ConvNeXt-B, matrix, Sapiens2 หรือ color เอง
