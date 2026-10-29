# CPI OOM — สาเหตุ การแก้ไข และผลตรวจจริง

**DIAGNOSTIC_PASS** · ปิดรอบเวลาไทย `2026-10-29T22:48:52.969845+07:00` · run `cpi-memory-repair-20261029T153956552075Z`. แก้จุดที่ล้มเหลวและทดสอบผ่านแล้ว ยังไม่เปิด full validation ใหม่

## สาเหตุ

VRAM ที่เห็นว่างหลังโปรแกรมหยุดคือหน่วยความจำที่ process คืนแล้ว ไม่ใช่ค่าขณะ OOM. CUDA usable รอบนี้ประมาณ14.56GiB แม้ nvidia-smi แสดง physical15360MiB. โค้ดเดิมขยาย parsing logits ของ instance candidates ทุกตัว ×20classes พร้อมกันผ่าน aligned_bilinear/F.pad/interpolate และมี intermediate tensors หลายก้อนซ้อนกัน.

ภาพ `0003218` มี **65 candidate instances** ไม่ได้แปลว่ามีคนจริง65คน. Actual low-resolution logits `[65,20,100,148]`, stride8, resized image800×1163, original344×500. Float grid ทั้งก้อนก่อน extra padding เท่ากับ4.587GiB. ครั้งที่ล้มCUDAขอ4.64GiB ขณะ free3.80GiB, allocated6.88GiB/reserved9.40GiB. Allocatedเป็นส่วนหนึ่งของreserved ไม่บวกสองค่านี้. ข้อผิดพลาดอยู่ใน native postprocessing/upsampling ไม่ใช่หลักฐานว่า weights107,444,791parametersใช้15GiBด้วยตัวเอง.

ยังไม่แยกสัดส่วน allocator fragmentation/live buffers ทั้งหมดจาก traceback เดิม และไม่ได้เปลี่ยน allocator/environment. การ empty_cache ไม่กำจัด live tensors ตาม [PyTorch memory management](https://docs.pytorch.org/docs/stable/notes/cuda.html#cuda-memory-management).

## วิธีแก้

เพิ่ม **CPI_PERSON_CHUNK_RESTORATION_1** เป็น model-local patch: aligned upsample/crop/original-grid resize/argmax ทีละcandidate แล้วเก็บhardmaskบนCPU. Gridต่อchunkเหลือ **72.27MiB** แทน4.587GiBทั้งก้อน แต่ยังทำครบทุกcandidateและ20channels. ไม่ลดmax_per_img/threshold/จำนวนคน; เป็น postprocessing person-axis chunk ไม่เปลี่ยนinput batch1.

คงcheckpoint/FP32/resolution/preprocessing/TTA/thresholds/align_corners=True/native classIDs/native PNG export/YOLO ownership/GT/scorerเดิม. ไม่มีFP16/CPU model inference/resolution fallback. Native CPU branch สำหรับoriginal dimension>2500pixelsคงเดิม ไม่ใช่fallbackที่เพิ่มใหม่และไม่เกิดในภาพที่ตรวจ. Sourceบนdisk/frozen configs/resultsไม่ถูกแก้.

## การตรวจและผล

- CPU4cases PASS: asymmetric literal/ties, native-operation referenceรวม7persons/stride8/crop/mapback/หลายchunks, nativeCPUbranch/empty, contract/noinputmutation. Nativehead replacement anchorตรง pinned sourceก่อนforward
- GPU synthetic7persons: native batch restorationเทียบchunkedให้hardlabelsตรงทุกpixel. ทุกactualframeเทียบfixed prefix2candidateกับnative GPU operationsตรง ไม่ใช้GTหรือคะแนนเลือกcandidate
- ใช้จริง **3 model-frame calls**: TRAINwarmup0000930หนึ่งครั้ง + VALdiagnostics0003218/0001641. Oneattemptต่อภาพ ไม่มีOOM/model retry/fallback
- NPZ readback/CRC/SHA/native20 integer/original geometry/GT bindings และsaved-mask scorer0.50/0.75ผ่าน. ภาพ0001641 **ทุกarrayตรงเดิม** รวมmasks/extents/boxes/confidence และNPZbytes/SHAตรงpacketเดิม; scoreJSONทั้งสองthresholdตรงเดิม

|ภาพ|บทบาท|ผล|Peak allocated MiB|Peak reserved MiB|
|---|---|---|---:|---:|
|0000930|Training|PASS|796.88|1252.00|
|0003218|Validation|PASS|9751.11|11726.00|
|0001641|Validation|PASS|8548.88|11726.00|

ภาพที่เคยOOM0003218ผ่านด้วย peak allocated **9.52GiB**, reserved **11.45GiB**. GPUทั้งprocessไม่ได้เหลือ72MiB เพราะยังมีupstream dynamic parsing/feature buffers. ค่าเดิม6.88/9.40GiBเป็นfailure-point observations ไม่ใช่completed-frame peaks จึงไม่ใช้เทียบเปอร์เซ็นต์ลดpeakของภาพนี้. Timing/resourceทั้งหมดเป็นdiagnostics ไม่จัดอันดับความเร็วหรือVRAM efficiency.

## ทางเรียกใช้และสิ่งที่ยังไม่รัน

[New ConvNeXt continuation](../scripts/run_cpi_chunked_continuation.py) reuse controller/reconciliation/atomic packets/guardsเดิมผ่าน wrapper แยก. Defaultตรวจอย่างเดียว; --executeเป็นmanualattemptใหม่. เพิ่มimplementationrevision/source/dependency/expandedworker hashes และeffective implementation fingerprint แยกจากbasefingerprintเก่า. ต้องมีGPUdiagnosticที่bindingsตรงกันและoldpacketregressionผ่าน. รวมdiagnostic time/storageใน24h/80GiB/free50GiB guards. ไม่reuse diagnostic predictionsเป็นcanonical.

คำสั่งสำหรับรอบที่เปิดต่อด้วยpatch (ยังไม่ได้เรียกในงานนี้):
```bash
.venvs/parser-legacy-cu113/bin/python Human_Parsing_Benchmark/scripts/run_cpi_chunked_continuation.py --model convnext --execute
```
เมื่อเปิดแล้วดูสถานะด้วยviewerใหม่:
```bash
.venvs/parser-legacy-cu113/bin/python Human_Parsing_Benchmark/scripts/run_cpi_chunked_continuation.py --model convnext --status --watch
```
ใช้detached executionตามworkflowเดิมบนserver. Original `run_cpi_continuation.py`ยังเก็บไว้และ**ไม่ได้ติดตั้งpatch** จึงอย่าใช้แทนwrapperใหม่เมื่อทดสอบวิธีนี้. [คำสั่งและประวัติ](../docs/CPI_CONTINUATION_COMMANDS_TH.md).

CPU controls ของwrapperใหม่2cases PASS: effectiveidentityหลังbaseidentityก่อนpacketcommit/patchก่อนwarmup/stop-on-errorคงอยู่; นับworker+diagnosticclocksครั้งเดียว. **ยังไม่ได้รันfullcontrollerใหม่บนGPU** หรือreconcile337ซ้ำเพื่อจัดรายงาน. First canonical patched packet/exact-ID reconciliationต้องตรวจเมื่อเปิดรอบจริง. การผ่าน2VALimagesไม่รับประกันทุกภาพ/ทุกkernelshape; upstreamforwardยังอาจOOMได้. ไม่มีautomaticretry/fallback/nextmodel.

Canonical ConvNeXtยัง **337/5000**, missing4663, primarynullตามSTRICT_COMPLETE. R50ยังพักและ**ยังไม่ทดสอบpatchบนGPU** แม้ใช้headร่วมกัน. Sapiens0.4B/0.8Bและผลเดิมทั้งหมดคงเดิม. ไม่เปิดfullbenchmark/training/color/CCTVหรือinferenceอื่นนอก3calls. GPUคืนหน่วยความจำหลังPID622542จบแล้ว.

## หลักฐาน

[CPU](../runs/cpi-memory-repair-20261029T153956552075Z/CPU_ACCEPTANCE.json), [GPU diagnostic / geometry / hashes](../runs/cpi-memory-repair-20261029T153956552075Z/GPU_DIAGNOSTIC.json), [controls](../runs/cpi-memory-repair-20261029T153956552075Z/CONTROL_ACCEPTANCE.json), [config](../configs/cpi_memory_diagnostic.json), [launch process](../runs/cpi-memory-repair-20261029T153956552075Z/PROCESS.json). KnownpacketSHA `a318aa843fc461b1f4d757374f6e81d13ce887e13334fffe265c57976f265a55`. Launchcommit `1bcea01ab9905bd3e55ea4c75cc89cb1d1efb960`; report/newCLIที่เพิ่มภายหลังเป็นpost-diagnostic snapshot ไม่ใช่launchcommit.

Rawhardmasks/nativeexports/attemptledger/logsอยู่ภายนอกpublicGitที่ `Human_Parsing_Benchmark/outputs/cpi_memory_diagnostics/cpi-memory-repair-20261029T153956552075Z` (launcherlogตามPROCESS.json); datasets/weights/environmentไม่ย้าย. ตรวจprotectedsource/config16ไฟล์ก่อน/หลังตรงเดิมตามconfig. ไม่bulkrehashทั้งinventoryหรือrescoreประชากรเพื่อทำรายงาน.

AdaptedoperationsจากCPI-Parser revisiond62cae523ba913fec4a7fda5816bc1d96bbf644d, headSHA `85b75e0fe38465ec460107c11111702345a6de091a8ba3d399ca266878ca7573`. Attributionในcode/testsและ[Apache2license](../provenance/licenses/CPI-Parser-APACHE-2.0.txt); firstpartylicenseไม่เปลี่ยน.
