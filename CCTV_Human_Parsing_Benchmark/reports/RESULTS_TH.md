# CCTV partial-annotation benchmark — สถานะและผลจริง

ชุดนี้มี 90 ภาพ ไม่ใช่100; annotateเฉพาะบางคน/บางส่วน และยังไม่มีกติกาDress. พื้นที่GT0เป็นUNKNOWNไม่ใช่negative. คะแนนหลักคือmacro recall4เฉพาะพิกเซลที่มีlabel; ไม่ใช่full-imageIoU/precision/personF1หรือคำรับรองผู้ชนะโดยรวม.

|Model|Status|Complete|Face recall %|Hair recall %|Upper recall %|Lower recall %|Macro recall %|
|---|---|---:|---:|---:|---:|---:|---:|
|QANet_CIHP_HRNetW48_512x384|COMPLETE|90/90|81.238|84.847|87.832|74.962|82.220|
|M2FP_R101_CIHP|COMPLETE|90/90|76.073|81.629|80.933|70.529|77.291|
|D2FP_R101_CIHP|NOT_STARTED|0/90|N/A|N/A|N/A|N/A|N/A|
|RPR_CIHP|NOT_STARTED|0/90|N/A|N/A|N/A|N/A|N/A|
|CPI_R50_CIHP|NOT_STARTED|0/90|N/A|N/A|N/A|N/A|N/A|
|CPI_ConvNeXtB_CIHP|NOT_STARTED|0/90|N/A|N/A|N/A|N/A|N/A|
|Sapiens2_0.4b|NOT_STARTED|0/90|N/A|N/A|N/A|N/A|N/A|
|Sapiens2_0.8b|NOT_STARTED|0/90|N/A|N/A|N/A|N/A|N/A|
|Sapiens2_1b|NOT_STARTED|0/90|N/A|N/A|N/A|N/A|N/A|

ทุกระบบใช้inputpopulationเดียวกัน, frozenYOLOcheckpoint/settings/cacheเดียวกัน, nativeFP32settings/threshold/TTA/map-backเดิม. QANetYOLOROI, Sapiensfull-frame+YOLOmaskownership, nativeinstanceparsers+YOLOassociationเป็นapplicationconfigurationcomparison ไม่ใช่architecture-onlytest. ไม่มีGTช่วยinference.

Face_Neckเป็นproxy; Upper/Lowerคือagreementกับannotationชุดนี้ ไม่ยืนยันnon-Dressboundary. OTHER/unknownpredictionclassesต้องไม่หายก่อนoverlap. Unlabeledpixelsไม่คิดFPหรือFN, ดังนั้นoversegmentationนอกlabelsไม่ถูกลงโทษและใช้recallเลือกdeploymentwinnerไม่ได้. ผลday/nightอยู่privatecanonicalMETRICS; ไม่มีspeed/VRAMranking.

STRICT_COMPLETE: primaryเฉพาะระบบที่ครบexactpopulation; failed/blockedไม่เอาsubsetมาแทน. Model/OOMretry0 ไม่มีprecision/resolutionfallback. เก็บpackets/hash/metadata/attemptlogsในprivateoutputs; ไม่เผยแพร่CCTVassets/filenamesบนGit. รอบเดิมในdataset/resultsเป็นexploratoryคนละroute/scoring ไม่ใช้รวมคะแนน.

ก่อนทำfullbenchmarkสำหรับเลือกผู้ชนะ ต้องมีsharednegative/ignore/complete-targetannotationpolicy, DressguidelineและQA/GTที่freezeแล้ว และfull-personextentsหากต้องการinstanceF1. การตั้งค่าประเมินไม่สร้างGTส่วนที่ขาดขึ้นมา.
