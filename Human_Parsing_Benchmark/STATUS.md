# Human Parsing Benchmark — current status

Updated **2026-10-29T13:04:01.363721+07:00 Bangkok (UTC+07)**

**CPI_COMMANDS_PREPARED / NO_NEW_INFERENCE / COMMON_PILOT_PASS_PRESERVED**

- ผู้ใช้ขอคำสั่ง CPI สองรุ่น: [คำสั่ง manual continuation](docs/CPI_CONTINUATION_COMMANDS_TH.md). CPU5cases PASS; reconciliation-only R50 3/5000 และ ConvNeXt-B 113/5000 PASS ใน environment CPI เดิม ยังไม่เปิด worker/warmup
- ผลใหม่จากการเรียกคำสั่งจะอยู่ `Human_Parsing_Benchmark/outputs/cpi_continuations/` ผลเดิมคงตำแหน่งเดิม ไม่รับรองว่า OOM หายแล้ว ไม่มี auto restart และไม่รันสองตัวพร้อมกัน

**Completed milestone: COMMON_C4P_04B_PILOT_PASS / SEVEN_CALL_BUDGET_CONSUMED / FULL_EVALUATION_NOT_AUTHORIZED**

- [รายงานปิดimplementation/pilot](reports/CIHP_SAPIENS_04B_PILOT_TH.md) เป็นcurrententry; [revision2protocol](protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json)
- Sapiens2_0.4b: warmup1+VAL6/6PASS,รวม7calls,parentsetup0calls+current7;failed/invalidVAL0,noOOM/retry/fallback. Detachedworker222281exited,queueหยุด
- Firstsetupinvalidเป็นuint8binary0/1vsboolassertก่อนforward(strictloadPASS,modelcalls0);preserveallhistory. Losslessbinarycachefixvalidated,noinferencepolicychange
- CPU23independentcases+4savednativepacketintegrations+7actualfrozenYOLOcacheprobesPASS. Geometrycanonicaltieswithidenticalgeometrylimits;C3globalonly,noQ_C3/secondpersondenominator
- GT-only5,000bindingscomplete:G_loc17,520,G_sem_C4=17,454. Pilot6GTpersons/eligible23. Fullcommon5,000scoresNOTCOMPUTED/primarynull
- Saved-maskrescore/atomicNPZ/sourcegeometry/hash/GTbindings/extentparitywithQANet6imagesboththresholdsPASS;visualinspection6done(notindependenthumanQA)
- NativefourCOMPLETE5,000eachpreserved;CPIbothPAUSED_NOT_CANCELLED/3+113successfulIDs/allOOMhistory/mainnullunchanged

Run `common-c4p-pilot-20261029T010410394659Z-binary-cache-fix`;launchcommit`a7683da4b4ad5bfe4a248aba168d74a1cdc24391`. Gallery `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/common_view/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/gallery/index.html` (private/externalGit).

Next: ผู้ใช้เลือกเรียก CPI manual command ทีละรุ่นได้; งานเตรียมคำสั่งครั้งนี้ไม่เปิด inference ให้เอง การเรียก `--execute` จึงเป็น manual attempt ใหม่ที่บันทึกแยก ไม่ใช่ automatic retry. ข้อเสนอ full common-view ยังต้องอนุมัติแยก **Do not restart Sapiens pilot: 7 calls consumed.** No automatic CPI/0.8B/1B/full-common/training/color/CCTV/YOLO inference.
