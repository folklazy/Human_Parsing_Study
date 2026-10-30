# สรุปตรวจปิดรอบ Human Parsing สำหรับส่งให้ผู้ช่วยตรวจต่อ

ตรวจเมื่อ **2026-10-30T10:44:14.373500+07:00 (เวลาไทย UTC+07)** — สถานะ **EXECUTION_COMPLETE / HANDOFF_READY_WITH_LIMITATIONS**

## ข้อสรุปและสิ่งที่คำว่าเสร็จหมายถึง

**งาน inference ของ checkpoints ทั้ง 9 ตัวมี canonical results ครบตัวละ 5,000 ภาพแล้ว**: QANet, M2FP, D2FP, RP-R-CNN, CPI R50, CPI ConvNeXt-B และ Sapiens2 segmentation 0.4B / 0.8B / 1B ไม่มี worker ของโครงการทำ inference อยู่ในขณะตรวจ GPU snapshot `0, Tesla T4, 0 MiB, 14912 MiB, 0 %` เป็นสถานะเฉพาะเวลาตรวจ ไม่รับรองว่าว่างตลอดไป; tmux sessions เดิมที่เหลือเป็น shell/session ไม่ใช่หลักฐานว่า worker ยังรัน

แยกผลเป็นสองงาน: **native20 ครบ 6 ระบบ**, **common C4-P revision2 ครบ 7 ระบบ** (QANet/M2FP/D2FP/RP-R-CNN + Sapiens3ขนาด) มี 4 checkpoints อยู่ทั้งสองตาราง จึงเป็น 9 unique checkpoints ไม่ใช่ 13 checkpoints และ **ยังไม่มี common C4-P ของ CPI ทั้งสอง** ห้ามเรียกว่าทั้ง9เปรียบเทียบใน common view เดียวกันครบแล้ว

รอบตรวจนี้ไม่รัน inference, tests ใหม่, full rescore หรือ bulk NPZ hash scan; ใช้ canonical completion/metrics, terminal ledgers, score-file membership และ audits ที่ตรวจรับไว้ ตรวจรายละเอียดได้ใน [VERIFICATION.json](../runs/closure-review-20261030/VERIFICATION.json) การตรวจนี้ไม่ใช่การรับรอง evaluator ทุกพิกเซลซ้ำโดยอิสระ

หลักฐานการตรวจกลไกก่อนรันยังอยู่ที่ [native readiness](CIHP_NATIVE_READINESS.md), [common CPU acceptance/pilot 0.4B](CIHP_SAPIENS_04B_PILOT_TH.md), [memory repair ของ CPI](CPI_MEMORY_REPAIR_TH.md) และรายงาน Sapiens [0.8B](CIHP_SAPIENS_08B_C4P_RESULTS_TH.md) / [1B](CIHP_SAPIENS_1B_C4P_RESULTS_TH.md) ใช้อ่านร่วมกับ completion ไม่ถือว่าจำนวน tests ที่ผ่านแทนความถูกต้องทางนิยามทุกกรณี หรือเป็นการรับรองโค้ดอิสระรอบใหม่

## ประชากรและกติกาที่ต้องคงไว้

ใช้ **official CIHP Validation 5,000 IDs** เท่านั้นสำหรับคะแนน ไม่ใช่ TRAIN, TEST หรือ CCIHP main4,961/reference5,000 รุ่นก่อน การ warmup TRAIN0000930 ไม่ใช่ training และไม่รวมคะแนน VAL ทั้งสองตารางใช้ภาพเดิมคนละ metric definition ไม่ได้เพิ่ม dataset เป็น10,000ภาพ

Frozen YOLO26x เป็น baseline/conditioning/identity ที่ใช้จริง ไม่มีการเลือก YOLO ใหม่ native scientific config SHA256 `3b6c98ef8056bc24c0a503559972619b7cb82bcf40cdfa2983579a84567c5a24`; population SHA256 `0bf366ae6fcde0967f915e1803bc08dbce94de5753e3dea9f0dbe5aa570083d7` Common protocol revision2 SHA256 `7fb101672407d465885efcc00202af927e93cd422daeae42bf215cbe504cd33d`; GT binding manifest SHA256 `1a6f635ffdd0da1b767a6d7279e0437130bdfdd47e510fbfdaeb9b047cc82cc0`

STRICT_COMPLETE: คะแนนชุดเต็มมีสิทธิ์รายงานเมื่อครบ exact5,000 unique IDs พร้อม artifacts/scoring ที่ตรวจรับแล้ว; unresolved failure/invalid/missing ให้ primary null ไม่ใช้ subset แทนชุดเต็ม ประวัติ failed attempts ยังเก็บไว้แม้ภายหลังทุก ID มีผลที่ใช้ได้

## 1. Native CIHP20 application results — หกระบบครบ

เรียง frozen roster order ไม่เรียงคะแนน ค่าเปอร์เซ็นต์ในรายงานปัด3ตำแหน่ง; CSV/JSON เก็บfraction0–1เต็มprecision

|ระบบ|สถานะ / จำนวน|mIoU20 รวม BG (%)|FG19 mIoU (%)|
|---|---|---:|---:|
|QANet_CIHP_HRNetW48_512x384|COMPLETE 5,000/5,000|64.866|63.449|
|M2FP_R101_CIHP|COMPLETE 5,000/5,000|68.155|66.796|
|D2FP_R101_CIHP|COMPLETE 5,000/5,000|64.352|62.827|
|RPR_CIHP|COMPLETE 5,000/5,000|59.124|57.408|
|CPI_R50_CIHP|COMPLETE 5,000/5,000|57.551|55.769|
|CPI_ConvNeXtB_CIHP|COMPLETE 5,000/5,000|65.411|63.954|

IoU_c=TP_pixels/(TP_pixels+FP_pixels+FN_pixels) สะสม population confusion ก่อนหาร mIoU20 เฉลี่ย20classesรวมBG; FG19เฉลี่ยIDs1–19เท่ากัน zero-union=0ตามnative reference policy GT total support876,659,024 pixels ประเมิน Dress6 เป็น Dress ไม่แบ่งupper/lower; background0 valid, GT255 shared ignoreตามprotocol

ผลนี้เป็น **YOLO-conditioned / YOLO-associated application pipelines** ไม่ใช่ official native-parser reproduction ทุกระบบ QANetใช้YOLO ROIและYOLOmaskownership/clipping; M2FP/D2FP/RPR/CPIใช้native full-frame/internalinstancesหรือqueriesแล้วprediction-only YOLOassociation ไม่ได้ใช้YOLOpixelclipแบบQANetทุกระบบ ความต่างจึงรวมcheckpoint/training/preprocessing/adapter/ownership ไม่แยกผลarchitectureเพียงอย่างเดียว

Native per-person: G_loc=17,520, G_sem=17,520; mask-IoU matching0.50/0.75ตามnative scorer Q_person_sem_GT ให้missed GT contribution0แล้วหารG_sem; unmatched predictionsไม่ได้ลงโทษQโดยตรง ต้องอ่านFP/F1ร่วม ExtentF1ไม่ใช่parsingAPหรือparserownershipaccuracyที่แยกจากdetector

|ระบบ|Mask IoU|TP|FP|FN|Extent F1 (%)|Q_GT (%)|
|---|---:|---:|---:|---:|---:|---:|
|QANet_CIHP_HRNetW48_512x384|0.50|16,906|7,156|614|81.314|61.454|
|QANet_CIHP_HRNetW48_512x384|0.75|15,304|8,758|2,216|73.609|57.130|
|M2FP_R101_CIHP|0.50|16,163|2,119|1,357|90.291|57.730|
|M2FP_R101_CIHP|0.75|15,318|2,964|2,202|85.571|55.859|
|D2FP_R101_CIHP|0.50|15,972|2,176|1,548|89.559|55.244|
|D2FP_R101_CIHP|0.75|14,817|3,331|2,703|83.083|52.725|
|RPR_CIHP|0.50|16,214|3,351|1,306|87.442|55.627|
|RPR_CIHP|0.75|14,470|5,095|3,050|78.037|51.458|
|CPI_R50_CIHP|0.50|15,819|3,896|1,701|84.968|55.669|
|CPI_R50_CIHP|0.75|13,855|5,860|3,665|74.419|50.889|
|CPI_ConvNeXtB_CIHP|0.50|16,288|2,880|1,232|88.792|61.144|
|CPI_ConvNeXtB_CIHP|0.75|15,026|4,142|2,494|81.912|57.854|

รายclass IoU/support/unionครบ20classes×6ระบบ: [NATIVE_PER_CLASS.csv](../metrics/closure-review-20261030/NATIVE_PER_CLASS.csv) และภาพรวมเต็มprecision [NATIVE_SUMMARY.csv](../metrics/closure-review-20261030/NATIVE_SUMMARY.csv)

## 2. Common C4-P revision2 — เจ็ดระบบครบ

ทุกแถว COMPLETE5,000/5,000 ใช้fixed GT domain/mapping/matcher revisionเดียวกัน; สี่ระบบแรกอ่านsaved artifacts ไม่inferenceซ้ำ Sapiensใช้full-frame native29 → original-grid map-back → frozenYOLOmaskownership ไม่ใช่nativepersonIDs

|ระบบ|mIoU4 (%)|Face proxy|Hair|Upper non-Dress|Lower non-Dress|C3 global (%)|
|---|---:|---:|---:|---:|---:|---:|
|QANet_CIHP_HRNetW48_512x384|80.984|87.695|79.919|81.870|74.452|78.747|
|M2FP_R101_CIHP|83.623|88.111|82.760|85.563|78.056|82.127|
|D2FP_R101_CIHP|82.610|87.423|82.006|84.303|76.706|81.005|
|RPR_CIHP|78.747|84.794|77.708|81.356|71.131|76.732|
|Sapiens2_0.4b|75.827|72.196|80.101|76.736|74.278|77.038|
|Sapiens2_0.8b|74.618|72.648|78.942|75.867|71.015|75.275|
|Sapiens2_1b|72.759|70.175|77.427|71.778|71.657|73.621|

C4-P mIoU4 เฉลี่ย Face proxy/Hair/Upper non-Dress/Lower non-Dress เท่ากัน C3เป็นglobal mean Hair/Upper/Lowerเท่านั้น ไม่มีQ_C3 อ้างนิยาม/complete native-ID projectionจาก [protocol revision2](../protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json) และ [ข้อเสนอ common-view](CIHP_SAPIENS_COMMON_VIEW_PROTOCOL_TH.md) ค่าunionต้องมาจากmappedconfusion ไม่ใช่เฉลี่ยnativeIoUเพื่อรวมคลาส

Face proxyยอมรับความต่างCIHPFaceกับSapiensFace_Neck ยังไม่ใช่strictface-only/annotationequivalence UpperคือCIHPUpperClothes+Coat เทียบSapiensUpper_Clothing; LowerคือPants+SkirtเทียบLower_Clothing Dress/ApparelยังvalidOTHER ไม่แบ่งด้วยheuristic ไม่มีper-modelignore BGและOTHERเป็นvalidnon-target ทำนายtargetบนOTHERเป็นFP, ทำนายOTHERบนtargetเป็นFN Faceยังvalidnon-targetในC3 ไม่voidเพื่อช่วยคะแนน

Common person G_loc=17,520, G_sem_C4=17,454 จากGT-only bindings ไม่ยกnativeG_sem17,520มาใช้ Matchinggeometry-canonical revision2รวมtie/ambiguitypolicyต่างจากnativehistoricalmatcher Q_C4_GTให้missed GT0และหาร17,454; ไม่ลงโทษunmatchedpredpersonsโดยตรง ExtentsSapiens/QANetมาจากfrozenYOLO จึงห้ามอ้างnativeinstancecapabilityจากextentparity

|ระบบ|Mask IoU|TP|FP|FN|Extent F1 (%)|Q_GT (%)|
|---|---:|---:|---:|---:|---:|---:|
|QANet_CIHP_HRNetW48_512x384|0.50|16,906|7,156|614|81.314|73.474|
|QANet_CIHP_HRNetW48_512x384|0.75|15,304|8,758|2,216|73.609|67.937|
|M2FP_R101_CIHP|0.50|16,163|2,119|1,357|90.291|69.591|
|M2FP_R101_CIHP|0.75|15,318|2,964|2,202|85.571|67.101|
|D2FP_R101_CIHP|0.50|15,972|2,176|1,548|89.559|68.018|
|D2FP_R101_CIHP|0.75|14,817|3,331|2,703|83.083|64.566|
|RPR_CIHP|0.50|16,214|3,351|1,306|87.442|68.640|
|RPR_CIHP|0.75|14,470|5,095|3,050|78.037|62.987|
|Sapiens2_0.4b|0.50|16,906|7,156|614|81.314|57.789|
|Sapiens2_0.4b|0.75|15,304|8,758|2,216|73.609|53.966|
|Sapiens2_0.8b|0.50|16,906|7,156|614|81.314|55.106|
|Sapiens2_0.8b|0.75|15,304|8,758|2,216|73.609|51.579|
|Sapiens2_1b|0.50|16,906|7,156|614|81.314|49.242|
|Sapiens2_1b|0.75|15,304|8,758|2,216|73.609|46.466|

Fullprecision summary: [COMMON_SUMMARY.csv](../metrics/closure-review-20261030/COMMON_SUMMARY.csv); person metrics/denominatorsทั้งสองview: [PERSON_METRICS.csv](../metrics/closure-review-20261030/PERSON_METRICS.csv) รายtarget GT supportเหมือนกันทุกแถว: Face37,932,488; Hair40,760,850; Upper148,199,276; Lower38,702,345 pixels supportเป็นGTpixels ไม่ใช่unionหรือจำนวนคน ค่าzero-union/OTHER/owner-unknownใช้revision2 ไม่มีเปลี่ยนจากผลคะแนน

## 3. CPI ที่เคยหยุด และหลักฐานประวัติที่ต้องส่งต่อ

- CPI ConvNeXt-B ปิดรอบ `convnext-20261029T160359716460Z` ครบ5,000: reuse337+new4,663; missing/duplicate/failed/invalidปัจจุบัน0 เก็บfailed attemptsเดิม3รายการ รุ่นแก้memory `CPI_PERSON_CHUNK_RESTORATION_1` สตรีมคืนพิกัดรายcandidateโดยคงnativeoperators/precision/settings
- CPI R50 ปิดรอบ **`r50-20261029T183615747685Z`** ครบ5,000: reuse912+new4,088; missing/duplicate/failed/invalidปัจจุบัน0 มีfailed attemptsเดิม5รายการเก็บไว้ ไม่ใช่ประวัติไม่เคยOOM ใช้ `CPI_FEATURE_BRANCH_SCHEDULE_3` bindingsตรวจตรงกับlaunchcommitและsourceปัจจุบัน โดยคง FP32/thresholds/geometry/scoring ไม่มีอ้างว่าตัวเลขจากรอบ912เป็นfinal
- R50จบ 2026-10-30T02:56:12.293575+07:00 รายงานเดิม [912-image attempt](cpi-r50-feature-20261029T175338825178Z.md) ยังถูกต้องในฐานะhistoricalattempt แต่ไม่ใช่currentresult ขณะตรวจพบSTATUS/READMEยังชี้912จึงแก้navigationเท่านั้น ไม่แก้attemptเดิมหรือเติมคะแนนย้อนหลัง
- Sapiens0.8Bมีretainedledger FAILEDที่0006307ขั้นMODEL_LOAD (CUDA OOM) ก่อนปิดรอบสำเร็จ จึงไม่ใช้finalfailed0อ้างว่าไม่เคยมีerror รอบนี้ไม่ลบ/แก้attemptledgerและไม่ตรวจรับเหตุผลการrestartย้อนหลังแทนผู้review
- บางSapiens COMPLETION.jsonมีfield `primary:null` ที่ไม่ได้อัปเดตเป็นตารางผล ให้ใช้ **METRICS.json → primary** คู่กับstatus/membershipตรวจผ่าน ไม่แปลnullfieldนี้เป็นคะแนน0หรืออ้างว่าคะแนนชุดเต็มไม่มี

CPI semantic mappingยังเป็น **ACCEPTED_WITH_INDIRECT_EVIDENCE** ไม่ยกระดับDIRECT_VERIFIED ผลย้อนหลังและsourceGT/frozenconfigsไม่เขียนทับ

## 4. สิ่งที่ตรวจจริงในการปิดงานรอบนี้

1. ตรวจprocess/GPUและterminalcompletionปัจจุบัน ไม่มีเปิดworker/controllerเพิ่มหรือรันโมเดลใด
2. NativeQANet/M2FP/D2FP: อ่านassembled terminalledgers exact5,000unique IDs เทียบofficialmanifest และmetricsตรงcanonicalparent ส่วนRPR reusepreviousfinalaudit/NPZ/saved-maskPASSและexact-IDevidenceในcompletion ไม่ทำfullauditซ้ำ
3. CPIสองตัว: compactCOMPLETIONตรงrawCOMPLETION; รวมverified_idsจากreuse/final RECONCILED audits exact5,000unique ตรงpopulation, reused/pendingdisjoint, exit0/queuestopped ไม่มีใช้counterเก่าแทนmembership
4. Commonเจ็ดตัว: completionและMETRICS COMPLETE5,000; terminal/reusedledger IDsและscorefilenamesครบpopulation ไม่มีduplicates; protocolhash/GTsupportตรงกัน ตรวจarithmeticmIoU/C3/Qnumerator-denominatorจากcanonicalstatistics ไม่มีคำนวณscorerใหม่
5. อ่านGTbindingmanifestและตรวจhashตรงconfig; ตรวจsmallsourcebindingsของR50ตรงlaunchcommit/sourceจริง ไม่rehashweights/datasets/bulkpacketsทั้งหมด ไม่อ้างexecutionacceptanceใหม่จากการตรวจเอกสาร

## 5. Canonical evidence และการทำซ้ำ

|View / ระบบ|Run / segment|Canonical completion|Canonical metrics|
|---|---|---|---|
|native20 / QANet_CIHP_HRNetW48_512x384|`cihp-native-six-20261028T034103254470Z`|[COMPLETION.json](../runs/cihp-native-six-20261028T034103254470Z/COMPLETION.json)|external assembled METRICS; SHA ใน verification|
|native20 / M2FP_R101_CIHP|`cihp-native-six-20261028T034103254470Z`|[COMPLETION.json](../runs/cihp-native-six-20261028T034103254470Z/COMPLETION.json)|external assembled METRICS; SHA ใน verification|
|native20 / D2FP_R101_CIHP|`cihp-native-six-20261028T034103254470Z`|[COMPLETION.json](../runs/cihp-native-six-20261028T034103254470Z/COMPLETION.json)|external assembled METRICS; SHA ใน verification|
|native20 / RPR_CIHP|`rpr-cihp-shared-20261028T155439603873Z`|[COMPLETION.json](../runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-shared-20261028T155439603873Z/COMPLETION.json)|[COMPLETION.json](../runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-shared-20261028T155439603873Z/COMPLETION.json)|
|native20 / CPI_R50_CIHP|`r50-20261029T183615747685Z`|[COMPLETION.json](../runs/r50-20261029T183615747685Z/COMPLETION.json)|[COMPLETION.json](../runs/r50-20261029T183615747685Z/COMPLETION.json)|
|native20 / CPI_ConvNeXtB_CIHP|`convnext-20261029T160359716460Z`|[COMPLETION.json](../runs/convnext-20261029T160359716460Z/COMPLETION.json)|[COMPLETION.json](../runs/convnext-20261029T160359716460Z/COMPLETION.json)|
|C4-P / QANet_CIHP_HRNetW48_512x384|`common-c4p-full-20261029T063458522990Z`|[COMPLETION.json](../runs/common-c4p-full-20261029T063458522990Z/QANet_CIHP_HRNetW48_512x384/COMPLETION.json)|[METRICS.json](../runs/common-c4p-full-20261029T063458522990Z/QANet_CIHP_HRNetW48_512x384/METRICS.json)|
|C4-P / M2FP_R101_CIHP|`common-c4p-full-20261029T063458522990Z`|[COMPLETION.json](../runs/common-c4p-full-20261029T063458522990Z/M2FP_R101_CIHP/COMPLETION.json)|[METRICS.json](../runs/common-c4p-full-20261029T063458522990Z/M2FP_R101_CIHP/METRICS.json)|
|C4-P / D2FP_R101_CIHP|`common-c4p-full-20261029T063458522990Z`|[COMPLETION.json](../runs/common-c4p-full-20261029T063458522990Z/D2FP_R101_CIHP/COMPLETION.json)|[METRICS.json](../runs/common-c4p-full-20261029T063458522990Z/D2FP_R101_CIHP/METRICS.json)|
|C4-P / RPR_CIHP|`common-c4p-full-20261029T063458522990Z`|[COMPLETION.json](../runs/common-c4p-full-20261029T063458522990Z/RPR_CIHP/COMPLETION.json)|[METRICS.json](../runs/common-c4p-full-20261029T063458522990Z/RPR_CIHP/METRICS.json)|
|C4-P / Sapiens2_0.4b|`common-c4p-full-20261029T063458522990Z`|[COMPLETION.json](../runs/common-c4p-full-20261029T063458522990Z/Sapiens2_0.4b/COMPLETION.json)|[METRICS.json](../runs/common-c4p-full-20261029T063458522990Z/Sapiens2_0.4b/METRICS.json)|
|C4-P / Sapiens2_0.8b|`sapiens08-c4p-20261029T081254180014Z`|[COMPLETION.json](../runs/sapiens08-c4p-20261029T081254180014Z/COMPLETION.json)|[METRICS.json](../runs/sapiens08-c4p-20261029T081254180014Z/METRICS.json)|
|C4-P / Sapiens2_1b|`sapiens1b-c4p-20261029T200113781375Z`|[COMPLETION.json](../runs/sapiens1b-c4p-20261029T200113781375Z/COMPLETION.json)|[METRICS.json](../runs/sapiens1b-c4p-20261029T200113781375Z/METRICS.json)|

ทุกsourceที่อ่านพร้อมSHA/ขนาดอยู่ใน [VERIFICATION.json](../runs/closure-review-20261030/VERIFICATION.json) ส่วนR50finalcompactrecordsที่ยังไม่publicในตอนเริ่มตรวจจะsyncพร้อมงานส่งมอบนี้ Gitcommitส่งมอบเป็นpost-run review snapshot ไม่ใช่launchcommit; launchcommitsแต่ละระบบอยู่canonicalrecords

Working copyหลักคือ `Human_Parsing_Benchmark/`; publiccheckoutแยก `Human_Parsing_Study_Public/` Shared assetsอยู่ `datasets/`, `models/`, `.venvs/`, source `third_party/human_parsing/` Bulk nativebatchเก่าอยู่ `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/` (ชื่อlocationเก่าไม่ได้ทำให้datasetกลายเป็นMHP-v2) CPIcontinuationsใหม่อยู่ `Human_Parsing_Benchmark/outputs/cpi_continuations/`; commonoutputsอยู่ `Human_Parsing_Benchmark/outputs/common_view/` อ้างแต่ละrunข้างต้น ไม่มีย้าย/ลบผลเดิม

Clonepublicrepoอย่างเดียวตรวจเอกสาร/โค้ด/compactresultsได้ แต่ไม่reproduceGPUbenchmarkโดยไม่มีexternaldataset/weights/env/nativeoutputs PublicGitไม่มีdatasetimages/weights/bulkmasks/rawlogs/CCTVassets Fullprobability/nativeconfidenceevaluationบางชนิดทำย้อนหลังไม่ได้จากhardmasks

## 6. ภาพและไฟล์ที่ควรส่งให้ Chat

**ส่งไฟล์ .md นี้เป็นทางเข้าหลัก** มีตารางnative6/common7/personทั้งสองthresholdและข้อจำกัดในตัว หากต้องตรวจตัวเลขเต็มprecisionให้แนบCSVสี่ไฟล์ใน `metrics/closure-review-20261030/`; หากต้องตรวจprovenanceให้แนบVERIFICATIONหรือเปิดcanonicallinks ไม่จำเป็นต้องส่งrawlogs/dataset/weightsทั้งหมด

ภาพอยู่privateบนserver ไม่อัปโหลดdatasetassetsสู่publicGitอัตโนมัติ:

- Nativeสี่ระบบ16ภาพ: `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/presentations/presentation-four-20261028T184321049969Z/index.html`
- Commonfixedsamplegallery: `Human_Parsing_Benchmark/outputs/common_view/common-c4p-full-20261029T063458522990Z/gallery/index.html`
- Sapiens1Bpilot6ภาพ: `Human_Parsing_Benchmark/outputs/common_view/sapiens1b-c4p-20261029T200113781375Z/pilot/gallery/`

ตรวจว่าindex/โฟลเดอร์ดังกล่าวมีจริง ไม่ได้renderภาพใหม่หรือตรวจpixelalignmentทุกpanelใหม่ในรอบนี้ galleryแต่ละชุดเป็นsnapshotเฉพาะระบบที่ระบุในmanifest ไม่ได้อ้างว่ามีภาพครบ9ระบบในหนึ่งแผง LegacyPRESENTATION_BUNDLE.zipเป็นsnapshotสี่โมเดลเก่า **ไม่ใช่ชุดผลล่าสุดทั้งหมด** หากแนบภาพในChatต้องใช้ไฟล์ที่ผู้ใช้มีสิทธิ์และส่งพร้อมmanifest/IDเพื่อระบุชุด

## 7. ข้อจำกัดและงานที่ยังไม่เสร็จ

- **ยังไม่ใช่overallwinner/selectedconfigurationสำหรับCCTV**: จำนวนครบเป็นexecutioncompleteness ไม่ใช่absolutequalitypass ยังต้องreviewผล/mandatorycapabilitiesและtrade-offsที่ตกลงไว้ ไม่รวมnative20กับC4-Pหรือใช้Qสูงสุดเพียงตัวเดียวตัดสิน
- **CPIยังไม่มีC4-P common scores** หากต้องการเทียบ9checkpointในtask4targetsเดียวกันต้องมีงานsaved-artifact common evaluationของCPIพร้อมcompatibility/readinessตรวจรับแยก ไม่จำเป็นต้องinferenceใหม่เพียงเพราะแปลงhardlabels และยังไม่ได้ทำในรอบนี้
- Commonprotocolออกแบบหลังเห็นผลสี่โมเดล ไม่อ้างpreregistered/independentfinalconfirmation Mappingยึดนิยาม ไม่tuneตามคะแนน Faceproxy/non-Dress/route/trainingexposureยังจำกัดคำอ้าง ความสำเร็จCIHPไม่ยืนยันCCTV/color/domaintransfer
- **ไม่มีclean latency/FPS/VRAM-efficiency ranking**: sharedGPUและtimingboundariesต่างกัน รวมCPI nativefileI/O การเก็บresourceobservationsไม่ทำให้costfairnessผ่าน
- Ninjaยังdeferred; color/attributes/CCTV/trainingยังไม่ดำเนิน ไม่เปิดงานเพิ่มอัตโนมัติจากรายงานนี้

ขั้นถัดไป: ส่งรายงานนี้และCSVที่ต้องการให้ผู้reviewตรวจนิยาม/ตัวเลข/หลักฐาน แล้วสั่งงานวิเคราะห์หรือขยายcommonCPIเฉพาะขอบเขตที่ต้องการ ไม่มีinference/retry/experimentใหม่ถูกเปิดจากการตรวจปิดรอบนี้
