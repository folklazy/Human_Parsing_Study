# CPI OOM — bounded memory repair

สถานะ **CPU_ACCEPTANCE_PASS / GPU_DIAGNOSTIC_PENDING** เวลาไทย `2026-10-29T22:39:56.552075+07:00`. Run `cpi-memory-repair-20261029T153956552075Z`. [Config](../configs/cpi_memory_diagnostic.json), [CPU acceptance](../runs/cpi-memory-repair-20261029T153956552075Z/CPU_ACCEPTANCE.json).

สาเหตุที่ยืนยันจากsource/tracebackคือ nativeheadขยายNคน×20classes×H×Wพร้อมกันผ่านaligned_bilinear/F.pad/interpolate; intermediate tensorsขนาดหลายGiBซ้อนกับlive tensors. ล่าสุด0003218ขอ4.64GiBขณะfree3.80GiB,allocated6.88/reserved9.40GiB. ไม่ใช่ข้อสรุปว่าweightsกิน15GiB และVRAMว่างหลังprocessหยุดไม่ใช่freeขณะerror. ใช้หน่วยGiB/MiBตามบันทึกCUDA; allocatedเป็นส่วนหนึ่งของreserved.

แก้ด้วยmodel-localmethodpatchที่ทำrestoration/argmaxทีละperson แต่คง20channels/ทุกคน/FP32/spatialgrids/interpolationalign_corners=True/scorethresholdsและnativeexport/YOLOassociation. ไม่เปลี่ยนsourceบนdisk/checkpoint/nativeconfig/scorer/frozenresults. NativeCPUbranchสำหรับoriginalimage>2500pixelsคงเดิม ไม่ใช่fallbackที่เพิ่มใหม่. มีnewimplementationfingerprint ไม่อ้างว่าhashเดิมครอบคลุมpatch.

CPU4oraclesผ่าน: asymmetricliteral/ties, nativeoperationreferenceรวม7persons/หลายchunks/stride8/crop/mapback, originalCPUbranch/empty, contract/inputimmutability. Nativeheadreplacementanchorตรง pinnedsource; GPUsynthetic/actualpacketregressionยังรอตรวจ. Diagnosticสูงสุด3modelframecalls: TRAIN0000930,failedVAL0003218,knownsuccessVAL0001641; oneattemptต่อภาพ,stopfirsterror,noautomaticretry/fullbenchmark. Actualprefix2personsเทียบnativeall-prefixGPUกับchunkedในทุกframe และknownsuccessต้องเทียบทุกsavedarrayตรงเดิม ไม่ใช้GT/คะแนนปรับsettings.

Rawprediction/log/nativefilesอยู่นอกGitที่`Human_Parsing_Benchmark/outputs/cpi_memory_diagnostics/cpi-memory-repair-20261029T153956552075Z`. คงfree50GiB/80GiB/24hcumulative; resourceclockเดิม389.4s,retainedเดิม27368778bytes. ก่อนlaunchตรวจGPU/process/diskอีกครั้ง; shared-qualityอนุญาตแต่ไม่รับประกันmemory. ผลnativeConvNeXtยัง337/5000mainnull, R50พัก,Sapiens0.4B/0.8Bครบและไม่แตะ.

Attribution: ใช้restorationoperationsจาก CPI-Parser revision `d62cae523ba913fec4a7fda5816bc1d96bbf644d`; adaptedportionsตาม[Apache2.0](../provenance/licenses/CPI-Parser-APACHE-2.0.txt). ไม่เปลี่ยนfirst-partyprojectlicense. [PyTorch memory management](https://docs.pytorch.org/docs/stable/notes/cuda.html#cuda-memory-management)แยกallocatedกับreserved;การempty_cacheไม่ใช่การกำจัดlive tensorsที่จำเป็น. ยังไม่อ้างแก้OOMครบทุกภาพหรือรับรองR50GPUexecution.
