# Human Parsing Benchmark — current status

Updated 2026-10-29T00:53:49.685389+07:00 Bangkok

**CPI_R50_MANUAL_CONTINUATION_INCOMPLETE / QUEUE_STOPPED**. ดำเนินการรันต่อตามผู้ใช้สั่งแล้วหนึ่งsegment; warmupผ่านแต่VAL0000018เกิดCUDA OOMซ้ำ ไม่มีผลใหม่เพิ่ม

- Reused3 / newcomplete0 / uniquecomplete3/5000; failedunique1,invalid0,notattempted4996,missing successful4997,duplicate0
- Historicalfailedattempt1 + currentfailedattempt1 =2OOMattemptsที่IDเดียวกัน; เก็บทั้งสองครั้ง ไม่ลบประวัติ
- **STRICT_COMPLETE main scoresnull**, no subset ranking. OriginalFP32/scientificsource/config/YOLOcache/GT/scorer unchanged. Shared GPU admission used; no timing/VRAMranking
- Round `cpi-r50-manual-continuation-20261028T175036811629Z`, launchcommit `dd02e228ebd215c034a785d41ea459f7db336bfd`; controller166181/worker166185 exited. No automatic retry or ConvNeXt-B

[รายงานส่งตรวจต่อ](reports/CIHP_CONTROLLED_CONTINUATION.md) / [completion](runs/cihp-native-six-20261028T034103254470Z/cpi-r50-manual-continuation-20261028T175036811629Z/COMPLETION.json) / [manual outcome](runs/cihp-native-six-20261028T034103254470Z/cpi-r50-manual-continuation-20261028T175036811629Z/MANUAL_CONTINUATION_OUTCOME.json) / [attempt history](runs/cihp-native-six-20261028T034103254470Z/cpi-r50-manual-continuation-20261028T175036811629Z/ATTEMPT_HISTORY.json)

ดูสถานะ `python3 Human_Parsing_Benchmark/scripts/cpi_r50_progress.py --watch` รวมreused3แล้ว; phaseSTOPPED_INCOMPLETE. Rawlogs/status: `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/rounds/cpi-r50-manual-continuation-20261028T175036811629Z/`

Next: รายงานOOMที่เกิดซ้ำจริง; การแก้peakmemoryต้องมีevidenceและคงscientificcontract ไม่เปิดrestartวน/ลดresolution/FP32หรือเริ่มโมเดลอื่นเอง QANet/M2FP/D2FP/RPRเดิมยังครบและไม่ถูกinferenceซ้ำ
