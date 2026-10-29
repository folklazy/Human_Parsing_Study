# Human Parsing Benchmark — current status

Updated **2026-10-29T07:51:06.417630+07:00 Bangkok (UTC+07)**

**COMMON_VIEW_PROTOCOL_PROPOSED_NOT_FROZEN / FOUR_NATIVE_RESULTS_PRESERVED / CPI_PAUSED_NOT_CANCELLED**

- งานปัจจุบัน: [ข้อเสนอ C4-P และแผนตรวจ implementation](reports/CIHP_SAPIENS_COMMON_VIEW_PROTOCOL_TH.md) พร้อม [draft spec](protocol/CIHP_SAPIENS_COMMON_VIEW_DRAFT.json)/[49-ID mapping](protocol/CIHP_SAPIENS_COMMON_VIEW_LABELS.csv). วัด CIHP target-output agreement สี่ช่อง; Face_Neck เป็น approximate Face proxy ไม่ strict equivalence; OTHER valid/domain เดียวกัน
- ข้อเสนอทำหลังผลสี่ระบบ ไม่ preregistered และไม่ใช้คะแนนเลือกmapping; ไม่ freeze/implement/execute จากเอกสารนี้
- ตรวจsourceที่pin, GT16masks/spot2images, existingpacketfields4 และ canonical20×20confusions4 แบบread-only; ไม่projectconfusionหรือcomputecommonscore. [Evidence](runs/common-view-proposal-20261029T004437Z/EVIDENCE.json), [consistency](runs/common-view-proposal-20261029T004437Z/CONSISTENCY_CHECKS.json)
- Pilotที่เสนอเท่านั้น: Sapiens2_0.4b,6preselectedVALdiagnosticIDs+≤1TRAINwarmup (≤7calls),ยังไม่อนุมัติ/เปิด; CPUpacket→scorer→reporterexpectedcasesเป็นข้อกำหนด ยังไม่implemented/tested

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

Next: reviewข้อเสนอหลัก C4-P operational claim และมอบหมาย implementation แยกจาก frozennativecode: totalmapping/fixedGTdomain, independentCPUexpectedcases,materializedG_loc/G_sem,route/export/readiness จากนั้น pilot เฉพาะเมื่อได้รับคำสั่งแยก ไม่เริ่มจากpermissionsเก่า CPIพัก; minimumstrictface/upper-lowerDressยังไม่ได้พิสูจน์
