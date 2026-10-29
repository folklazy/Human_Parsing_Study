# ผล Human Parsing บน native CIHP: สี่ระบบที่ครบ และข้อเสนอ class mapping เบื้องต้น

สถานะ ณ **2026-10-29T01:58:50.095263+07:00 เวลาไทย UTC+07** · work unit `presentation-four-20261028T184321049969Z` · **4/6 ระบบครบ** · รายงานเพื่อเตรียมนำเสนอ ไม่ใช่ผลครบเก้ารุ่นหรือการรับรองพร้อมใช้งาน CCTV

## 1. สรุปสำหรับนำเสนอ

- ศึกษา pretrained checkpoints/configurations สำหรับ body parts เสื้อผ้า และ accessories ที่รองรับ ใช้ frozen YOLO26x เป็นองค์ประกอบของ application pipeline และ native CIHP official validation **5,000 IDs / 17,520 GT persons**
- QANet, M2FP, D2FP และ RP-R-CNN มี canonical completion ครบทุก ID ผลสี่ระบบตรวจผ่านแล้วก่อนงานนี้ รอบนี้อ่าน metrics เดิมและตรวจความตรงของตาราง ไม่ทำ inference หรือ full rescore ใหม่
- **M2FP เป็น semantic quality leader ในสี่ configuration ที่ครบนี้:** mIoU20 **68.155%**, FG19 **66.796%** และ IoU สูงสุดทุก native class20 ในตารางนี้ เป็นผล configuration ร่วมกับ route/preprocessing/training ไม่ใช่ข้อพิสูจน์ว่า architecture เพียงอย่างเดียวเหนือกว่า
- **QANet ให้ Q_person_sem_GT สูงกว่า** แต่มี FP มากกว่า จึงห้ามเรียกผู้ชนะจาก metric เดียวว่า overall winner; ยังไม่ประกาศ selected configuration สำหรับ phaseถัดไปหรือ absolute pass ด้านงานจริง
- CPI R50 และ ConvNeXt-B **พัก ไม่ได้ยกเลิก**: เก็บ successful IDs และ OOM history ทั้งหมด คะแนนหลักยัง `null` ไม่ใช้คะแนน subset มาเทียบกับ5,000 ภาพ
- ผู้ใช้เปลี่ยนลำดับเป็น **สรุปสี่ตัว + matrix ก่อน CPI ครบ** การจัดทำ matrix หลังมีผลบางโมเดลต้องยึดนิยามคลาส ไม่เลือก projection เพื่อเพิ่มคะแนน ไม่มี common-view scores ใหม่ ไม่มี Sapiens2/color/CCTV inference ในรอบนี้

## 2. Protocol และสิ่งที่คะแนนวัด

แหล่งกติกาคือ [PLAN](../PLAN.md), [frozen scientific config](../configs/cihp_native_six.json), [population](../manifests/CIHP_NATIVE_VALIDATION.json), [native readiness](CIHP_NATIVE_READINESS.md) และ [operational history](CIHP_CONTROLLED_CONTINUATION.md) Frozen config SHA256 `3b6c98ef8056bc24c0a503559972619b7cb82bcf40cdfa2983579a84567c5a24`, population SHA256 `0bf366ae6fcde0967f915e1803bc08dbce94de5753e3dea9f0dbe5aa570083d7` เก็บเหมือนเดิม

Native semantic labels20 รวม background0, ignore255 ตามsource; readiness พบเฉพาะ0–19 ในVALจึงไม่มี255ที่สังเกตได้ Dress6ยังเป็นDress ไม่ใช่FaceMaskของCCIHP Original GT/officialsplitไม่แก้ และไม่ใช้CCIHP/Ninja projectionsหรือ4,961ประชากรเก่ามาปะปน คะแนนรอบนี้เป็น **YOLO-conditioned/associated application comparison บน native CIHP GT** ไม่ใช่ official native-parser reproduction ทุกระบบ

| Configuration | Input / identity / ownership ที่ใช้จริง |
|---|---|
|QANet HRNet-W48|ROIAlign รับ predictedYOLO boxes; native outputกลับoriginalgrid แล้ว clip semanticด้วยcachedYOLO masks; finalextentและpersonidentityมาจากYOLO ไม่มีnativeinstanceparserให้เทียบเป็น0คน|
|M2FP R101 / D2FP R101|Nativefullframe human/partqueries; เก็บnativehumanmasks/semanticplanes ภายใต้nativeoverlapresolution แล้วเลือกด้วยprediction-onlyYOLO bboxassociation ไม่มีการclipด้วยYOLOmaskเพิ่ม|
|RP-R-CNN R50|Nativefullframeพร้อมinternaldetector; parsingforegroundเป็นextent แล้วprediction-onlyYOLOassociation ไม่มีGTช่วยprediction|

AssociationกับYOLOใช้ **bboxIoU0.50**; finalprediction↔GT matchingใช้ **person maskIoU0.50/0.75** เป็นคนละขั้น Matchingเลือกจำนวนคู่สูงสุดก่อนผลรวมIoU และใช้stableIDเพื่อtie Globalsemanticcompositeเลือกforegroundของfinalpersonตามpersonscoreที่ประกาศไว้ ไม่เปลี่ยนownershipหลังดูGT ROI conditioning กับnative+associationเป็นความต่างของconfigurationที่ต้องเปิดเผย ไม่ใช่การแยกผลbackbone/training/adapterได้ทั้งหมด

## 3. สถานะทั้งหกและคะแนนหลัก

เรียงตาม **frozen roster order**; ตัวเลขIoUทั้งหมดด้านล่างเป็น **เปอร์เซ็นต์**, ส่วน CSV/JSON เก็บ fraction 0–1 เต็ม precision; ช่อง CSV ว่างใช้แทน JSON null/N/A และอ่านเหตุผลจาก missing_main_score_reason `null`หมายถึงไม่มีคะแนนหลักที่มีสิทธิ์ ไม่ใช่0 ชุดเต็มยังคงทุกระบบที่รันไม่ครบ

|ระบบ|สถานะงาน / execution|Complete/expected|Failed / invalid / not-attempted|mIoU20 รวมBG (%)|FG19 mIoU (%)|
|---|---|---:|---:|---:|---:|
|QANet HRNet-W48 512×384|COMPLETE / COMPLETE|5,000/5,000|0 / 0 / 0|64.866|63.449|
|M2FP R101 CIHP|COMPLETE / COMPLETE|5,000/5,000|0 / 0 / 0|68.155|66.796|
|D2FP R101 CIHP|COMPLETE / COMPLETE|5,000/5,000|0 / 0 / 0|64.352|62.827|
|RP-R-CNN R50 CIHP|COMPLETE / COMPLETE|5,000/5,000|0 / 0 / 0|59.124|57.408|
|CPI_R50_CIHP|PAUSED_NOT_CANCELLED / INCOMPLETE|3/5,000|1 / 0 / 4,996|null / N/A|null / N/A|
|CPI_ConvNeXtB_CIHP|PAUSED_NOT_CANCELLED / INCOMPLETE|113/5,000|1 / 0 / 4,886|null / N/A|null / N/A|

แหล่งตาราง: [COHORT_STATUS.csv](../metrics/presentation-four-20261028T184321049969Z/COHORT_STATUS.csv); ต้นฉบับคือ canonical metrics/completion ที่ระบุใน provenance ไม่ใช่ข้อความแชทหรือค่าที่ปัดเศษไว้ก่อน จำนวนCPIยืนยันจากexecutionledgersของcohortนี้ ไม่รวมdiagnosticหรือhistoricalCPIต่างprotocol

### แหล่ง run / segment / resource policy

|Model ID|Run/segment ที่ผลมาจาก|Resource policy|Canonical completion|
|---|---|---|---|
|QANet_CIHP_HRNetW48_512x384|`cihp-native-six-20261028T034103254470Z`|ORIGINAL_NO_CONTENTION_ADMISSION; exclusive runtime not certified|`runs/cihp-native-six-20261028T034103254470Z/COMPLETION.json`|
|M2FP_R101_CIHP|`cihp-native-six-20261028T034103254470Z`|ORIGINAL_NO_CONTENTION_ADMISSION; exclusive runtime not certified|`runs/cihp-native-six-20261028T034103254470Z/COMPLETION.json`|
|D2FP_R101_CIHP|`cihp-native-six-20261028T034103254470Z + continuation-20261028T073741308461Z`|ORIGINAL_NO_CONTENTION_ADMISSION; exclusive runtime not certified; D2 concurrent external GPU PIDs observed in health log|`runs/cihp-native-six-20261028T034103254470Z/COMPLETION.json`|
|RPR_CIHP|`rpr-cihp-shared-20261028T155439603873Z`|SHARED_GPU_QUALITY_ONLY|`runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-shared-20261028T155439603873Z/COMPLETION.json`|
|CPI_R50_CIHP|`cpi-r50-manual-continuation-20261028T175036811629Z`|SHARED_GPU_QUALITY_ONLY|`runs/cihp-native-six-20261028T034103254470Z/cpi-r50-manual-continuation-20261028T175036811629Z/COMPLETION.json`|
|CPI_ConvNeXtB_CIHP|`cpi-convnext-validation-20261028T182116250459Z`|SHARED_GPU_QUALITY_ONLY|`runs/cihp-native-six-20261028T034103254470Z/cpi-convnext-validation-20261028T182116250459Z/COMPLETION.json`|

canonical completion ของparentเดิมเป็นhistorical3/6 แต่QANet/M2FP/D2FPแถวCOMPLETEและmetricsยังใช้ได้ ส่วนRP-R-CNNใช้completionจากroundแยก ไม่แก้parenthistoryให้ดูเหมือนทุกตัวจบsegmentเดียวกัน [Current index](../manifests/CIHP_NATIVE_COHORT_INDEX.json) เป็นnavigationderivedจากแหล่งเหล่านี้

## 4. IoU และ support ราย native class

IoU_c = TPpixels_c/(TPpixels_c+FPpixels_c+FNpixels_c), สะสมconfusionทั้งpopulationก่อนคำนวณ; mIoU20เฉลี่ย20classเท่ากัน, FG19เฉลี่ย1–19 ไม่ใช่per-imageaverageหรือfrequency-weightedscore Zero-unionตามreferencepolicyให้0 ไม่ให้1หรือเปลี่ยนคลาสที่averageตามโมเดล

GTpixel supportรวม **876,659,024 pixels** เท่ากันทุกระบบ; ตารางระบุGTpixelsของclassไม่ใช่จำนวนภาพหรือจำนวนคน Supportไม่เท่ากันจึงต้องแสดงร่วมกับIoU ไม่สรุปว่าrareaccessoryมีคุณภาพพอจากglobalaverage

|Native class ID/name|GT pixels|QANet IoU (%)|M2FP IoU (%)|D2FP IoU (%)|RP-R-CNN IoU (%)|
|---|---:|---:|---:|---:|---:|
|0 Background|533,617,773|91.784|93.974|93.321|91.733|
|1 Hat|5,562,258|72.153|75.848|72.845|65.660|
|2 Hair|40,760,850|79.919|82.760|82.006|77.708|
|3 Glove|522,334|42.048|49.100|40.546|34.535|
|4 Sunglasses|379,419|64.209|67.497|65.281|52.492|
|5 UpperClothes|84,893,554|68.613|72.412|71.253|66.722|
|6 Dress|17,351,843|56.552|61.974|59.524|54.788|
|7 Coat|63,305,722|65.739|69.991|68.901|64.193|
|8 Socks|1,286,257|37.532|41.155|36.390|33.105|
|9 Pants|35,769,654|74.967|78.585|76.781|71.629|
|10 Torso-skin|12,306,143|75.867|76.624|75.389|70.519|
|11 Scarf|1,913,574|40.051|46.090|40.287|38.180|
|12 Skirt|2,932,691|42.005|42.974|41.033|37.846|
|13 Face|37,932,488|87.695|88.111|87.423|84.794|
|14 Left-arm|13,247,145|72.711|77.285|73.046|65.796|
|15 Right-arm|14,680,267|72.556|77.617|73.667|67.048|
|16 Left-leg|3,138,137|69.411|70.351|63.971|58.296|
|17 Right-leg|3,102,484|69.458|71.755|63.906|59.589|
|18 Left-shoe|1,966,143|57.599|59.631|51.291|44.567|
|19 Right-shoe|1,990,288|56.454|59.372|50.179|43.283|

[PER_CLASS.csv](../metrics/presentation-four-20261028T184321049969Z/PER_CLASS.csv) มีIoU,GTsupport,predictedsupport,unionเต็มprecision ตัวหารIoUรายclassคือunion ไม่ใช่GTsupportอย่างเดียว M2FPมีค่าIoUสูงสุด20/20classในสี่ระบบนี้เป็นข้อสังเกตเชิงพรรณนา ยังไม่มีpaireduncertaintyintervalหรือstatisticalsignificanceจากการทดสอบใหม่

## 5. Person matching และ semantic ต่อคน

- `G_loc = 17,520`: nativeGTpersonsที่นำเข้าlocationmatching; `G_sem = 17,520` ในnative20ประชากรนี้: GTpersonsที่มีnativeforegroundsemantic support ไม่ควรนำตัวหารนี้ไปใช้กับcommon4targetsอัตโนมัติ
- TP/FP/FNนับpersonsจากmaskmatching; precision=TP/(TP+FP), recall=TP/G_loc, F1=2TP/(2TP+FP+FN) ไม่ใช่parsingAP/PCPและไม่ใช่parserownershipaccuracyที่แยกจากdetector
- `Q_person_sem_GT`: สำหรับแต่ละeligibleGTperson ใช้matchedpredpersonคำนวณmeanforegroundIoUของunionclasssetที่GTหรือpredictionมีจริง; missedGTpersonได้0 แล้วsum/G_sem จึงเป็นcoverage-awareไม่ใช่matched-onlyaverage
- Global semantic domain ใช้ GT labels 0–19 รวม BG ส่วน per-person semantic domain ยัง void พิกเซล GT category>0 แต่ Human_id=0 เพราะไม่ทราบเจ้าของร่วมกันทุกระบบ; Human_id>0/Category0 ยังคงเป็น background และไม่ลบ GT extent
- Unmatchedpredpersonsไม่ลงโทษQโดยตรง จึงต้องอ่านพร้อมFP/F1 QANetextentได้รับจากYOLOmaskและnativeparserอื่นใช้extentคนละที่มา; F1นี้วัดfinalapplicationextent/coverage ไม่ใช่ความสามารถสร้างnativeidentityของQANet

|ระบบ|GT-mask IoU threshold|TP persons|FP persons|FN persons|Precision (%)|Recall (%)|Extent F1 (%)|Q_person_sem_GT (%)|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|QANet HRNet-W48 512×384|0.50|16,906|7,156|614|70.260|96.495|81.314|61.454|
|QANet HRNet-W48 512×384|0.75|15,304|8,758|2,216|63.602|87.352|73.609|57.130|
|M2FP R101 CIHP|0.50|16,163|2,119|1,357|88.409|92.255|90.291|57.730|
|M2FP R101 CIHP|0.75|15,318|2,964|2,202|83.787|87.432|85.571|55.859|
|D2FP R101 CIHP|0.50|15,972|2,176|1,548|88.010|91.164|89.559|55.244|
|D2FP R101 CIHP|0.75|14,817|3,331|2,703|81.645|84.572|83.083|52.725|
|RP-R-CNN R50 CIHP|0.50|16,214|3,351|1,306|82.872|92.546|87.442|55.627|
|RP-R-CNN R50 CIHP|0.75|14,470|5,095|3,050|73.959|82.591|78.037|51.458|

[PERSON_METRICS.csv](../metrics/presentation-four-20261028T184321049969Z/PERSON_METRICS.csv) เก็บG_loc/G_sem/Q_numeratorพร้อมอัตรา ไม่มีcohortcontaminationaggregateในcanonicalmetricsชุดนี้ แม้per-framepacketมีmatchedcontaminationdiagnostics จึงไม่สร้างค่าcohortใหม่เพื่อเติมรายงาน และไม่อ้างว่าF1สูงพิสูจน์ownership/semanticsถูกทั้งหมด

### Native ungated semantic reference — รายงานแยกจาก application

ค่านี้มาจากผลnativeที่เก็บในinferenceเดิม ไม่ใช่additionalinferenceหรือระบบapplicationผู้ชนะ และQANetไม่มีnativeinstance/fullframe referenceนี้

|Configuration|Native ungated mIoU20 (%)|
|---|---:|
|QANet HRNet-W48 512×384|null / N/A|
|M2FP R101 CIHP|68.975|
|D2FP R101 CIHP|65.444|
|RP-R-CNN R50 CIHP|59.378|

## 6. สิ่งที่สรุปได้ และสิ่งที่ยังสรุปไม่ได้

**จากข้อมูลจริง:** M2FPมีglobalsemanticIoUและextentF1สูงสุดในสี่ระบบที่ครบ ส่วนQANetมีGT-personsemanticQสูงกว่าที่ทั้งสองthreshold และrecallสูงกว่าที่matchingthreshold0.50; ที่0.75 M2FPมีrecallสูงกว่าเล็กน้อย ขณะที่QANetมีFP7,156ที่threshold0.50เทียบM2FP2,119 จึงเป็นtrade-offจริง ตัวเลขเหล่านี้ไม่บังคับให้สร้างweightedscoreใหม่หรือเลือกoverallwinnerจากความรู้สึก

**คำอธิบายที่เป็นไปได้ ไม่ใช่ผลพิสูจน์สาเหตุ:** routeที่QANetรับYOLOROIและclipด้วยYOLOmaskอาจมีส่วนต่อcoverage/Q/FP; nativeparsersถูกกรองด้วยYOLOassociation ความต่างยังรวมcheckpointtraining/nativeTTA/resolution/threshold/postprocess จึงไม่แยกสาเหตุarchitectureได้

**ยังไม่ได้ทดสอบ:** uncertainty/tie,cleanlatency/FPS/joint-residencyVRAMranking,CCTVdomaintransfer,color/attributes,common-viewคุณภาพของSapiens2 การเลือกจากCIHPเป็นpublicselection evidence ไม่ใช่independentfinalconfirmationหรือคำรับรองแม่นพอใช้งานจริง

## 7. ชุดภาพเปรียบเทียบ 16 ภาพ — เก็บในเครื่องเท่านั้น

ใช้frozen16IDs/seed20261028ที่ล็อกก่อนVALscores และตรวจSHAตรงsnapshotเดิม ไม่เลือกจากคะแนน รอบนี้แสดงRGB/GT/fourmodelsในพิกัดเดียวกัน แถวบนnative20semanticoverlay แถวล่างHuman_ids/finalpersonextents paletteและlegendเดียวกัน สีperson/เลขpersonเป็นlocalIDsคนละpanel **ไม่ได้หมายถึงGTmatchingกัน** ที่ไม่มีสีoverlayคือเห็นRGBเดิม ไม่ใช่การทาสีclassforeground

ตรวจRGB/GTsourcehash,originalgeometryและselectedpacketSHA/metadata/labelcontract **64packets** (4×16) ผ่าน แสดงด้วยfrozencomposeเดิม NativePNGเต็มใช้originalgridไม่มีmaskresampling; JPEGpreviewsย่อเพื่อเปิดดูเท่านั้น ทุกrecordระบุsourcepacketและsegmentจริง [Visualization manifest](../runs/cihp-native-six-20261028T034103254470Z/presentation-four-20261028T184321049969Z/VISUALIZATION_MANIFEST.json) ชี้ตรวจย้อนกลับได้ ภาพจากparent/continuation/RPRroundแยกกันอย่างเปิดเผย

**ตำแหน่ง gallery บน server จาก workspace root:**

```text
Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/presentations/presentation-four-20261028T184321049969Z/index.html
Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/presentations/presentation-four-20261028T184321049969Z/panels/          # PNG full-resolution ทั้ง16
Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/presentations/presentation-four-20261028T184321049969Z/previews/        # JPEG preview
```

สำหรับดาวน์โหลดไปเตรียมสไลด์ มี private bundle `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/presentations/presentation-four-20261028T184321049969Z/PRESENTATION_BUNDLE.zip` รวมรายงาน ตาราง matrix และ gallery16ภาพ (ไม่รวม datasets/weights/raw predictions/environments) ภาพอยู่ในโฟลเดอร์ gallery ภายในZIP ไม่อัปโหลดbundleนี้ไปpublicGit โดยอัตโนมัติ

เปิดผ่านVSCodeportforwarding โดยรันคำสั่งนี้ในworkspace rootแล้วforwardport8765:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/presentations/presentation-four-20261028T184321049969Z
```

หลังเปิดserverจึงเข้า `http://127.0.0.1:8765/index.html` คำสั่งนี้เป็นstaticviewer ไม่เรียกmodel/inference ไฟล์ภาพไม่อยู่publicGitเนื่องจากนโยบายสิทธิ์redistributionเดิม; publiccloneอย่างเดียวเปิดภาพไม่ได้ ต้องใช้privategalleryที่เก็บในworkspace/สำเนาที่ผู้ใช้มีสิทธิ์เข้าถึง

สำหรับสไลด์เลือก **first frozen ID ของแต่ละGT-onlystratum** (people>=5×area>187500): `0021448`, `0019475`, `0001538`, `0001413` กฎเลือกกำหนดก่อนเปิดpredictionsในงานรายงานนี้ แต่หลังผลaggregateมีอยู่แล้ว; ทั้ง16ยังอยู่ในindexไม่ซ่อนภาพอื่น ภาพใช้ประกอบอธิบาย ไม่ใช้เปลี่ยนmapping/settings/ผู้ชนะ

|ตัวอย่างที่กำหนดด้วยstratum|ข้อสังเกตจากการเปิดภาพจริง|
|---|---|
|`0021448`|ฉากธงบังตัวคน: GT5คนและทุกระบบส่ง5finalextents แต่พื้นที่UpperClothes/Coatและขอบบริเวณวัตถุบังยังต่างกัน การนับ5maskไม่ยืนยันownershipถูกทุกพิกเซล|
|`0019475`|ฉากคนบังกัน: GT5คน, QANet/RP-R-CNN5finalextents, M2FP/D2FP4 ไม่ควรตีความจำนวนอย่างเดียวว่าphysicalpersonมี4คน จุด(60,230)GTUpperClothes5แต่ทั้งสี่ทำนายCoat7; จุด(100,250)GTCoat7แต่ทั้งสี่ทำนายUpperClothes5 (พิกัดภาพเดิมเริ่ม0) เป็นตัวอย่างclassboundary/category disagreementเทียบreleasedGT ไม่ใช่สาเหตุที่พิสูจน์แล้ว|
|`0001538`|คนสองคนชิดและซ้อนกัน: ทุกระบบส่ง2finalextents แต่เส้นแบ่งHair/Face/Torso-skin/UpperClothesบริเวณคอเสื้อและขอบเสื้อแตกต่างกัน ยังไม่ใช้ภาพนี้ยืนยันface/neck equivalenceข้ามtaxonomy|
|`0001413`|คนสี่คนขนาดเล็ก: GTและทุกระบบ4finalextents ควรดูรายละเอียดHat/Sunglasses/Faceและขอบมือ ไม่ใช้จำนวนmaskเท่ากันเป็นหลักฐานว่าทุกรายtargetถูกต้อง|

ตรวจภาพdetailแบบAI4ภาพที่เลือกและจุดlabel2ตำแหน่งจากsavedmasks ไม่ใช่independenthumanannotationreviewหรือdataset-wideerrorprevalence อีก12ภาพผ่านการตรวจhash/geometryเพื่อจัดแสดง แต่ไม่อ้างว่ามีhumanreviewละเอียด [Qualitative notes](../runs/cihp-native-six-20261028T034103254470Z/presentation-four-20261028T184321049969Z/QUALITATIVE_NOTES.json) ระบุขอบเขตและจุดตัวอย่างที่เลือกหลังดูภาพ ข้อแตกต่างเทียบreleasedGTไม่พิสูจน์ว่าคนจริงไม่มีอยู่หรือGTสมบูรณ์ทุกคน

## 8. ความเสี่ยงด้าน fairness และขอบเขตการอ้างผล

|ประเด็น|หลักฐาน/ข้อจำกัด|ผลต่อการตีความ|
|---|---|---|
|Exposure/split|Native readinessบันทึก39train–VALexactJPEGduplicategroups และwithinVALคู่0021594/0023177; populationหลักยังofficial5000|ไม่เรียกชุดนี้overlap-controlledหรือindependenttraining-exposure-free ไม่คัดภาพตามคะแนนหรือนำCCIHP4961มาใช้แทน|
|Checkpointtraining|ทั้งสี่เป็นCIHPweights แต่recipe/nativeaugmentation/releaseselectionhistoryและpretrainingexposureไม่ได้ควบคุมทั้งหมด; UNKNOWNไม่ใช่NO|เปรียบเทียบreleasedcheckpoint/configuration ไม่อ้างแยกผลarchitectureหรือข้อมูลฝึก|
|Route/ownership|QANetYOLOROI+maskclip vsnativefullframe+YOLOassociation|instanceF1และQต้องอ่านตามmasksources; noGT-assistedprediction|
|GTscope|Releasedannotationsเท่านั้น; readinessมีตัวอย่างvisiblebackgroundcrowdไม่annotated|FPคือเทียบreleasedGT ไม่ยืนยันว่าphysicalpersonไม่มีจริง; noannotationcleanclaimจากdecodepass|
|Classimbalance|IoUmacroเท่ากันทุกclass แต่pixel-supportต่างกัน|แสดงperclass/support; ไม่ใช้globalmIoUแทนความละเอียดaccessoriesทุกชนิด|
|GPU/runtime|D2มีconcurrentexternalPIDระหว่างrun;RPR/CPIshared explicitly;adaptertimingรวมI/Oต่างกัน|**ไม่จัดอันดับlatency/FPS/VRAMefficiency** ไม่เติมfull-routeFPSจากcachedYOLOreadtime|
|Failures|CPIสองตัวINCOMPLETE ต่างจากqualityinferiority|mainnullพร้อมfailurehistory ไม่ลบแถว ไม่เอาsubsetมาตัดสินแพ้ความแม่นยำ|
|Selection/posthoc|รายงานผล4/6ก่อนอีกสองตัวจบ;matrixจัดหลังมีผล|native20primaryfrozenไม่เปลี่ยน ข้อเสนอcommonmappingไม่เลือกด้วยคะแนน ไม่เรียกconfirmatory9-modelwinner|

## 9. Class mapping เบื้องต้น — ข้อเสนอ ยังไม่รัน

เอกสารเสนอใหม่สำหรับ **nativeCIHP** ไม่ใช่CCIHPdraftเก่า ไม่แก้activeprojection/configหรือcanonicalnative20scores [Native49-row projection matrix](../protocol/CIHP_SAPIENS_MAPPING_PROPOSAL.csv), [CIHP20↔Sapiens class relationships](../registry/CIHP_SAPIENS_CLASS_COMPATIBILITY.csv), [nine checkpoint bindings](../registry/CIHP_SAPIENS_CHECKPOINT_LABEL_BINDINGS.csv), [non-executable specification/sources](../protocol/CIHP_SAPIENS_MAPPING_PROPOSAL.json)

### ตรวจ actual IDs และหลักฐาน

- CIHPGT20ตามREADMEในarchive; M2FP/D2FPมีexplicitregistry0–19และHuman20แยกเป็นstructuredbranch **ไม่ใช่semanticclassที่21** Glove/Glovesเป็นspellingvariant
- QANet/RPR/CPIผูกnativeCIHP20config,source,checkpointและnumericrouteตามevidenceที่โครงการรับรองอยู่ ไม่ยกระดับเป็นDIRECT_VERIFIEDด้วยการอ่านชื่อในcatalog ไม่เปิดgateเดิมใหม่
- Sapiens2 **0.4B/0.8B/1B ตรวจแยกทุกconfig**: num_classes29,Class29datasetpath,sourceignore255 และlocalHFconfigมี29genericLABEL_n ชื่อจริงยืนยันกับpinnedDOME_CLASSES_29และofficialSEG.md ทั้งชุดตรงกัน Headerแต่ละsafetensorsมี`decode_head.conv_seg.weight` shape[29,64,1,1]/bias[29] ตรวจheaderเพียง44–74KBต่อไฟล์ ไม่โหลดโมเดลหรือhashweightsใหญ่ซ้ำ [Header evidence](../protocol/SAPIENS_SEGMENTATION_HEADER_EVIDENCE.json) ยืนยันจำนวนhead ไม่ได้ทำให้ชื่อคลาสออกมาจากweightsเอง
- ชื่อsourceและSHA/revisionที่อ่านจริงอยู่ในbinding/sourceevidence ไม่สมมติว่าtaxonomyเหมือนกันจากชื่อรุ่น ทั้งสามSapiensเป็นsemanticlabels ไม่ใช่nativepersonIDs และไม่มีinferenceใหม่ในงานนี้

`EXACT`ด้านล่างหมายถึงconceptที่จับคู่หนึ่งต่อหนึ่ง ไม่รับรองannotation/pixel-extent equivalence; `UNION`คือรวมnamedconceptsที่มีเหตุผล ส่วนboundaryevidenceแยกคอลัมน์ ไม่มีการรับรองจากชื่อคลาสเพียงอย่างเดียว

|เป้าหมายขั้นต่ำ/กรณีพิเศษ|CIHP GT และ native20 predictions|Sapiens29 prediction candidate|สถานะ/ข้อมูลสูญหาย|
|---|---|---|---|
|Hair|2 Hair|4 Hair|EXACTที่concept;ขอบเขตผม/occlusionยังไม่independentlyverified|
|Face|13 Face|3 Face_Neck ∪24–28 lips/teeth/tongue|PARTIAL_OVERLAP: facialpartsunionมีเหตุผลแต่เอาneckออกจากclass3ไม่ได้; CIHPface/neckpartitionยังไม่ชัด จึงไม่ประกาศstrictfaceequivalence|
|Uppercloth|5 UpperClothes ∪7 Coat|23 Upper_Clothing|UNIONฝั่งCIHPตามประเภทเสื้อผ้าบน ไม่ใช่anatomicalwaistcut; Sapiensbroadcategoryเทียบfineclassesเป็นPARTIAL_OVERLAP;coat/dresspartitionยังต้องตรวจ|
|Lowercloth|9 Pants ∪12 Skirt|13 Lower_Clothing|UNIONฝั่งCIHP; Sapiensไม่แยกpants/skirtและมีLower_Spandexใน34→29 จึงไม่reconstructnativefineclassได้|
|Dress|6 Dressคงnativeclass|1Apparelยังไม่verifiedDress;23/13ไม่ให้แบ่งDressGTเอง|UNKNOWN/INCOMPATIBLEสำหรับlosslessupper/lower split; ไม่ใช้bbox/ตำแหน่งแนวตั้ง/GTช่วยheuristics|
|Apparel|ไม่มีclassnativeCIHPที่เท่ากันโดยตรง|1 Apparel|source52→29มีHairnetและApparelเดิม;จึง**ไม่ใช่หลักฐานว่าApparel=Dressหรือallclothes** ขอบเขตส่วนอื่นยังUNKNOWN|
|Eyewear|4 Sunglasses|2 Eyeglass (frames/lensesunion)|PARTIAL_OVERLAP: regularglasses/sunglassescoverageไม่เท่ากันโดยนิยาม|
|Body/feet|Torso-skin/arms/legs|Torso,upper/lowerlimbs,hands/feet|ไม่ถือว่าสkin/anatomicalextentตรงกัน ต้องตรวจhand/footboundary ไม่มีการเพิ่มhardrequirementเอง|

หลักฐานเฉพาะจุดที่อ่านเพิ่มเติม: DOME52→29รวมgum/palate/eyebrow/eyelash/Face_Neck_Skinเข้าFace_Neck;INTERNAL32→29รวมnose/ears/eyes/browsในclass3 ดังนั้นการรวม24–28ช่วยเก็บรายละเอียดใบหน้าแต่ไม่แก้neck/regionboundaryที่หายไปและไม่พิสูจน์whole-faceequivalence

### ข้อเสนอ fixed domain และ projection ทั้งสองฝั่ง

เสนอcommonIDs **0BG,1FACE,2HAIR,3UPPER,4LOWER,5OTHER** สำหรับการreviewเท่านั้น: CIHP13→FACE,2→HAIR,5/7→UPPER,9/12→LOWER;Sapiens3/24–28→FACE,4→HAIR,23→UPPER,13→LOWER คลาสforegroundที่เหลือรวมDress/Apparel→**OTHERที่ยังvalid ไม่ใช่BG/VOID**

ใช้GTdomainเดียวกันทุกโมเดล: GTnative0–19validรวมBG;เฉพาะGT255voidเท่ากัน ไม่สร้างignoreจากprediction/โมเดล PixelGTOTHERยังเป็นnegativeevidenceของtarget:ทำนายtargetบนOTHERGTเป็นFP;ทำนายOTHERบนGTtargetเป็นFN Unknown/out-of-rangepredictionเป็นcontractfailure แต่recognizedApparel/Dressไม่ทำให้runINCOMPLETEเพียงเพราะไม่ใช่targetขั้นต่ำ

นี่วัดการส่งมอบnamedtargetตามprojection ไม่ใช่nativeaccuracyของSapiens โดยเฉพาะDressGTอยู่OTHERจึงไม่ได้วัดupper/lowerpartitionของเดรส และnativeoutputที่ถูกตามtaxonomyของตัวเองอาจไม่ตรงprojectedtask ต้องเปิดเผยtask-incompatibility ไม่ซ่อนด้วยper-modelignore

**ยังไม่พร้อมfreezecommon4-targetleaderboard:** face/neckและgarmentpartitionยังไม่equivalentชัดเจน เสนอให้ตรวจเป็นdiagnosticproposalก่อน การทำhair/upper/lowerสามtargetเป็นsupplementaryอาจใช้ศึกษาได้ แต่ไม่ถือว่าตัดFaceออกจากrequirementหรือผ่านminimumสี่targetแล้ว `G_sem`ของcommonviewต้องderiveใหม่รายคนจากGTprojection ไม่copy17,520 semanticdenominatorโดยอัตโนมัติ;G_locยังผูกnativeHumanIDs/fixedpopulation

### สิ่งที่ทำย้อนหลังได้/ไม่ได้

|จากartifactsที่มี|ขอบเขต|
|---|---|
|Hard-labelprojection/union|ทำได้จากnativeintegerplanesโดยคงownershipเดิม; composeด้วยnativeforeground/scoresก่อนproject ไม่ลบOTHERก่อนแก้overlap ในรอบนี้ยังไม่computecommon-viewคะแนน|
|PersonmatchingและFP/FN/Q|ทำใหม่ได้เมื่อcommonGTprojection/domain/eligibilityได้รับreviewและversioned; ไม่เปลี่ยนpredictionด้วยGT|
|Boundarydiagnostics|hardmasksเพียงพอสำหรับบางนิยาม แต่protocolปัจจุบันไม่ได้มีcohortBoundaryIoUที่รับรอง จึงไม่เพิ่มคะแนนใหม่ในรายงานนี้|
|Aggregateprobabilitiesก่อนargmax|ทำไม่ได้ทั่วไปจากargmaxhardlabels; unionหลังargmaxไม่เท่ากับsumprobabilitiesก่อนargmax|
|Allnativepartconfidence/APทุกแบบ|canonicalpacketsมีpersonscoresแต่ไม่เก็บfullperpixelprobabilities/partconfidencesทุกระบบ จึงไม่รับรองnativeAP/PCP/softmetricย้อนหลังทุกชนิด|
|NativeidentityของSapiens|semanticlabelsไม่สร้างpersonIDs ต้องระบุroute/conditioningก่อนอนุมัติในงานถัดไป ไม่ใช้YOLO/GTเดาเป็นnativecapability|

### Primary sources และrevisionที่ใช้

- [Native CIHP/PGN](https://github.com/Engineering-Course/CIHP_PGN) และlocaldatasets/CIHP/README.md; [PGN ignore convention](https://github.com/Engineering-Course/CIHP_PGN/blob/master/utils/image_reader.py) ใช้ประกอบbackground/ignore ไม่ใช่คู่มือbodyboundaryครบถ้วน
- [Sapiens2 official SEG definitions, pinned7e5bae8](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/docs/SEG.md) และ [DOME/source-to-target mappings](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/sapiens/dense/src/datasets/seg/seg_utils.py)
- M2FP registryrevision17a89decacfca347ed18bed66baec7a5847ea43c / D2FP9d415948de94b1a0bb74b18cfdace68dcd75acb8 มีdirectnumericcategories;QANet61615c4491979569771020bc4beff86d63974829 / RPRdfcc227723d4bf6566356cda4513a84ed9a8ba30 / CPId62cae523ba913fec4a7fda5816bc1d96bbf644d ใช้binding/evidenceเดิม [CSVbinding](../registry/CIHP_SAPIENS_CHECKPOINT_LABEL_BINDINGS.csv) และsourceSHAในproposalJSONระบุไฟล์จริงทุกตัว ไม่copythird-partycodeเพิ่มเข้ารายงาน

## 10. ปัญหา CPI และสถานะพัก

R50: successfulunique3,failedunique1ที่0000018,failedattempts2จากสองsegments (รวมVALattempts5) ล้มในcausalparsinghead; ConvNeXt-B: successfulunique113,failedunique1ที่0001218,failedattempt1,VALattempts114 ล้มในaligned_bilinear/F.padขยายlogits Diagnostic0000018ของConvNeXtผ่านแยกจากcanonicalและไม่รวมใน113;canonical0000018ก็ผ่านจริง การผ่านหนึ่งภาพไม่รับประกันภาพอื่น

นับจากledgeractualและเชื่อมcompletion/hash ไม่hardcodeจากแชท [CPI attempt counts](../metrics/presentation-four-20261028T184321049969Z/CPI_ATTEMPT_COUNTS.json) เก็บsuccessfulIDs/failureidentity; OOMหลักฐานเต็มใน [operational report](CIHP_CONTROLLED_CONTINUATION.md) และexternalrawroots ไม่สรุปOOMเป็นqualityinferiority หรือassertว่าexternalGPUเป็นสาเหตุเดียว ไม่มีOOMfix/retry/allocator/FP16/resolution/thresholdchangeในรอบนี้

## 11. สิ่งที่เสร็จและงานถัดไป

**เสร็จแล้ว:** canonical summary ของสี่ระบบ พร้อม per-class/person metrics,6rowsretained/CPIpausednull,16imagegalleryพร้อม4representatives/legend/provenance,9checkpointnumeric/sourcechecksและ49native-rowmappingproposalพร้อม20classrelationships ตารางนี้ไม่ได้ทำให้SapiensหรือCPIมีbenchmarkคะแนนใหม่

**ถัดไป:** reviewface/neck,upper/lower/Dress/Apparelและcommonvaliddomainจากนิยาม;ระบุfrozenprojection/claim/semanticeligibilityก่อนอนุมัติcommon-viewevaluationหรือSapiensรอบใหม่ CPIยังพักและแก้ทรัพยากรเป็นอีกคำสั่งได้ ไม่ต้องรอCPIครบเพื่อใช้ชุดสี่ตัวนี้นำเสนอ แต่ห้ามเรียกว่าครบเก้ารุ่นหรือfinalCCTVselectionแล้ว ไม่มีnewdataset/metric/training/color/CCTVงานเพิ่มโดยอัตโนมัติ

## 12. การตรวจซ้ำและreproduction limits

[Provenance](../runs/cihp-native-six-20261028T034103254470Z/presentation-four-20261028T184321049969Z/PROVENANCE.json) เก็บSHAcanonicalcompletion/metrics/ledgers/sourceconfig/sample/renderer;[exactreportdata](../runs/cihp-native-six-20261028T034103254470Z/presentation-four-20261028T184321049969Z/REPORT_DATA.json) เก็บค่าที่นำมาพิมพ์ตาราง ไม่มีตัวเลขจากroundedchat คำสั่งสร้างตาราง/ภาพคือ `python3`ของenvironmentที่มีnumpy/Pillow/SciPyแล้วรัน`scripts/build_four_model_presentation.py`; matrixใช้`scripts/build_cihp_sapiens_matrix.py` ทั้งสองเป็นreport-onlyไม่มีmodelinference แต่อาศัยexternaldatasets/checkpointsmetadata/savedpacketsและpathsในprovenance จึง**ไม่อ้างว่าclonepublicrepoอย่างเดียวreproducebenchmarkหรือเปิดภาพได้ทันที** ไม่rebuildเพียงเพื่อให้ชื่อworkunitเหมือนเดิม เพราะทุกครั้งสร้างfreshartifactdirectory

รูป16ภาพ/64selectedpacketsตรวจhash/geometryครั้งนี้;fullpopulationartifactvalidation/re-scoreใช้หลักฐานเดิมที่ยังตรงกัน ไม่ทำfullrescore/hashweights/datasetauditซ้ำเพื่อจัดเอกสาร รูปและprivatebundleอยู่externalGit;เฉพาะfirstpartycode,plans/proposals,CSV/JSONsmall/provenance/reportที่แจกจ่ายได้ถูกpublish

## ข้อเสนอ common view ฉบับดำเนินการต่อ (29 ตุลาคม2026)

อ่าน [CIHP–Sapiens C4-P protocol proposal](CIHP_SAPIENS_COMMON_VIEW_PROTOCOL_TH.md) สำหรับนิยามสี่target, OTHER/VOID, Face_Neck limitation, Sapiens routeและboundedpilotplan สถานะPROPOSED_NOT_FROZEN หลังเห็นผลสี่ระบบ ไม่มีcommonviewscore/inferenceใหม่ ตารางและcanonicalผลnativeข้างต้นไม่เปลี่ยน PrivateZIPเดิมเป็นsnapshotก่อนการชี้แจงถ้อยคำrecallครั้งนี้ ให้ใช้รายงานในGitrevisionปัจจุบันสำหรับข้อความที่แก้แล้ว
