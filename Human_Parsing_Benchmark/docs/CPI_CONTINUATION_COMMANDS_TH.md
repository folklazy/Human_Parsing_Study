> **Memory repair update:** ใช้ [repaired ConvNeXt wrapper](../scripts/run_cpi_chunked_continuation.py) สำหรับperson-chunkrestorationที่ผ่านdiagnostic; [report](../reports/CPI_MEMORY_REPAIR_TH.md). Original `run_cpi_continuation.py`ด้านล่างไม่ได้ติดตั้งpatch. ConvNeXt canonical337/5000; R50patchGPUยังไม่ทดสอบ. Executeเป็นmanuallaunch ไม่ใช่automaticretry.

# คำสั่ง CPI continuation สำหรับ operator

สถานะ 29 ตุลาคม 2026: ผู้ใช้ขอคำสั่งรัน CPI ทั้งสองตัว งานจัดเตรียมนี้ **ไม่ได้เปิด inference** และไม่ได้แก้ OOM หรือรับประกันว่าจะไม่เกิดซ้ำ ผล native สี่โมเดลและ Sapiens pilot ไม่เปลี่ยน

สคริปต์ใหม่ [run_cpi_continuation.py](../scripts/run_cpi_continuation.py) เป็น operational controller แยก ไม่แก้ frozen scientific worker/config เดิม การเรียก `--execute` เป็นการสั่ง manual attempt ใหม่เฉพาะโมเดลที่ระบุ รวม IDs ที่เคยล้มเหลวและยังไม่มีผลสำเร็จ ไม่มี automatic retry/fallback หรือการเปิดโมเดลถัดไป

## ใช้งาน

เรียกจาก workspace root ที่มี `Human_Parsing_Benchmark/`, `.venvs/`, `models/`, `datasets/` และ legacy artifacts อยู่ครบ ใช้ environment เดิมของ CPI เพื่อให้ saved-mask rescore เทียบผลเดิมได้ตรง ไม่ใช้ Python/environment ของ Sapiens แทน

ตรวจ/reconcile อย่างเดียว โดยไม่รันโมเดล:

```bash
.venvs/parser-legacy-cu113/bin/python Human_Parsing_Benchmark/scripts/run_cpi_continuation.py --model r50
.venvs/parser-legacy-cu113/bin/python Human_Parsing_Benchmark/scripts/run_cpi_continuation.py --model convnext
```

เปิด **ทีละตัว** ใน detached process; stdout append เพื่อเก็บประวัติ ส่วน segment และ worker log ใช้ directory ใหม่ทุกครั้ง:

```bash
mkdir -p Human_Parsing_Benchmark/outputs/cpi_continuations
nohup .venvs/parser-legacy-cu113/bin/python -u Human_Parsing_Benchmark/scripts/run_cpi_continuation.py --model r50 --execute >> Human_Parsing_Benchmark/outputs/cpi_continuations/r50-console.log 2>&1 < /dev/null &
```

เมื่อจะทำ ConvNeXt-B โดยไม่มี CPI ตัวอื่นทำงานอยู่:

```bash
nohup .venvs/parser-legacy-cu113/bin/python -u Human_Parsing_Benchmark/scripts/run_cpi_continuation.py --model convnext --execute >> Human_Parsing_Benchmark/outputs/cpi_continuations/convnext-console.log 2>&1 < /dev/null &
```

ดูความคืบหน้า; เปลี่ยน `r50` เป็น `convnext` เพื่อดูอีกตัว:

```bash
.venvs/parser-legacy-cu113/bin/python Human_Parsing_Benchmark/scripts/run_cpi_continuation.py --model r50 --status --watch
```

Ctrl+C ที่ viewer หยุด viewer เท่านั้น ไม่หยุด worker ไม่ใช้ viewer เดิมที่อ้าง pointer ของ historical rounds เพื่อดู segment ใหม่

## สิ่งที่ controller ทำ

- ล็อก CPI ร่วมกันทั้งสองรุ่นและตรวจ process เดิม ปฏิเสธการเปิด worker ซ้ำ สคริปต์เดิมที่ไม่ใช้ lock ยังต้องไม่เปิดเองพร้อมกัน
- ตรวจ frozen source/config/checkpoint/population และ source revision ใช้ verifier เดิมตรวจ NPZ/metadata/fingerprints/GT/saved scores ของ CPI ที่มีอยู่ ไม่อ่านผล QANet/M2FP/D2FP/RPR ทั้งชุดซ้ำ
- แยก diagnostic ออกจาก canonical IDs นับ diagnostic ใน resource history เท่านั้น ไม่เอาภาพ diagnostic มาเติมคะแนน validation
- สร้าง manifest แบบ pending/reused ที่ไม่ทับกัน รักษาลำดับ population เดิม และบันทึกผลเดิม/failed attempts ทุกครั้ง ไม่เลือก output จากคะแนน
- ใช้ resource wrapper เดิมสำหรับ SHARED_GPU_QUALITY_ONLY และ worker เดิมที่ hash-bound เพิ่มเฉพาะ allowed artifact path ไป workspace ปัจจุบัน เก็บ expanded source/control diff ก่อน launch
- คง FP32/preprocessing/resolution/TTA/threshold/batch/YOLO/ownership/scorer เดิม TRAIN warmup `0000930` หนึ่งครั้งต่อการเปิดโมเดล หยุดเมื่อเจอ error ไม่มี auto OOM retry/CPU fallback
- คง 24h ต่อ checkpoint โดยรวมเวลาของ worker attempts และ diagnostic ที่มี closed clocks, 80GiB ของข้อมูล stream ที่นับได้ และ disk guard 50GiB; ไม่อ้างว่าครอบคลุม disk ทั้ง workspace หรือเป็น storage forecast
- Reconcile และรวม sufficient statistics หลัง worker จบ ผลที่ครบเท่านั้นมี primary score ตาม STRICT_COMPLETE ค่า unresolved failed/invalid นับตาม ID และไม่ลบ failed-attempt history ที่ภายหลังสำเร็จแล้ว

## ตำแหน่งและหลักฐาน

- ผลใหม่: `Human_Parsing_Benchmark/outputs/cpi_continuations/<model>-<UTC>/` อยู่นอก Git
- ผลเดิม: ที่เดิม `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/` ไม่ย้ายหรือเขียนทับ
- `SEGMENT_PLAN.json`, `RESOURCE_POLICY.json`, `EXPANDED_WORKER.py`, `CONTROL_DIFF.patch` อธิบาย binding/control ก่อนรัน
- `LAUNCH.json`, `ROUND_STATUS.json`, `WORKER.log`, `segments/<model>/RUN.json`, `FRAMES.jsonl`, `packets/` ติดตาม worker/attempts
- `COMPLETION.json` หลังตรวจ artifacts เป็นผล canonical ของ continuation; เมื่อสำเร็จจะมี compact copy ใน `runs/<segment>/` และรายงาน `reports/<segment>.md` ด้วย ยังต้อง review ก่อน sync Git ตาม workflow เดิม
- หาก state เป็น `INCOMPLETE_REQUIRES_RECONCILIATION` ให้ตรวจ `CONTROLLER_FAILURE.json` และ artifacts ก่อนสั่งใหม่ ไม่วน restart อัตโนมัติ

## การตรวจที่ทำจริงก่อนส่งคำสั่ง

CPU orchestration fixtures 5 cases ผ่าน: failed→success reconciliation, failure attempts ซ้ำแต่ unresolved ID ไม่ซ้ำ, duplicate success rejection, invalid/failure ไม่ double count และ expanded worker คง stop/resource controls

Reconciliation-only ใน environment CPI เดิมตรวจ R50 3 IDs และ ConvNeXt-B 113 IDs ผ่าน เหลือ 4,997/4,887 ตามลำดับ ไม่ได้เริ่ม worker หรือ warmup การทดลอง reconcile ใน environment Sapiens ที่ใหม่กว่าพบ exact-score mismatch ใน native reference; environment CPI เดิมผ่าน จึงบังคับ environment ตรงก่อนตรวจ ไม่แก้ saved scores เพื่อให้ผ่าน

**ยังไม่ได้ตรวจ GPU execution ของ controller ใหม่นี้** การผ่าน CPU/reconciliation ไม่ยืนยันว่าจะไม่ OOM โดยเฉพาะภาพที่เคยล้มเหลว ค่า timing ยังคงเป็น shared-GPU adapter diagnostics ไม่ใช้จัดอันดับความเร็ว
