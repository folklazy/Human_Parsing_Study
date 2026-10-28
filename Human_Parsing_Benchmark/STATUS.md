# Human Parsing Benchmark — current status

Updated **2026-10-29T01:56:19.221143+07:00 Bangkok (UTC+07)**

**FOUR_MODEL_PRESENTATION_READY / CPI_PAUSED_NOT_CANCELLED / MAPPING_PROPOSAL**

- [รายงานภาษาไทยสำหรับส่งตรวจและนำเสนอ](reports/CIHP_FOUR_MODEL_RESULTS_TH.md) เป็นcurrentsummary authoritative; [currentcohort](manifests/CIHP_NATIVE_COHORT_INDEX.json)
- QANet/M2FP/D2FP/RP-R-CNN canonicalCOMPLETE **5,000 IDsตัวละชุด**, nativeGTpersons17,520; metricscopiedexactly,noinference/fullrescore
- CPI R50paused: successfulunique3,failedunique1/twoOOMattempts; ConvNeXt-Bpaused: successfulunique113,failedunique1/oneOOMattempt; mainnullทั้งสองSTRICT_COMPLETE เก็บledgers/packets/diagnostic/historyเดิมทั้งหมด
- เปลี่ยนลำดับตามผู้ใช้: สรุป4และdraftmappingก่อนCPIครบ ไม่ได้ยกเลิกCPI ไม่อนุมัติretry/inference/Sapiens/color/training/frozenconfigchange
- 16frozenqualitativeIDs,64selectedpackets hashes/geometrychecked,4GT-stratum-firstexamples AIspotinspected; ไม่อ้างindependenthumanreview16ภาพทั้งหมด
- [49-rowmappingproposal](protocol/CIHP_SAPIENS_MAPPING_PROPOSAL.csv), [20-classrelationships](registry/CIHP_SAPIENS_CLASS_COMPATIBILITY.csv), [9checkpointbindings](registry/CIHP_SAPIENS_CHECKPOINT_LABEL_BINDINGS.csv) อยู่สถานะproposal ไม่accepted/frozen/executable; Face/Neck/garmentpartitionยังเปิดเผยunknown
- No latency/FPS/VRAMefficiencyranking. Native20benchmarkผลคงเดิม; common-viewscoreและSapiensไม่รันในงานนี้

Privategalleryจากworkspace root:
`Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/presentations/presentation-four-20261028T184321049969Z/index.html`

Staticviewinstructionsและexactmetrics/provenanceอยู่ในรายงาน ไม่publishdatasetimages/rawpredictions/weightsไปpublicGit

Next: ใช้รายงาน/ชุดภาพนำเสนอและreviewmatrixตามclassdefinition; ตัดสินprojection/domain/eligibilityก่อนคำสั่งประเมินถัดไป CPIพักไว้ ไม่restartจากhistoricalpermissions ไม่มีmodelworkerของรอบนี้ขณะเริ่มreporting
