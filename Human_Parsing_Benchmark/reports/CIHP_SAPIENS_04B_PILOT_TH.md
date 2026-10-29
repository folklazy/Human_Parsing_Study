# รายงาน CIHP–Sapiens2 0.4B common-view implementation และ pilot

Work/run `common-c4p-pilot-20261029T010410394659Z` · Protocol `CIHP_SAPIENS_C4P / revision-2-pilot` · Updated 2026-10-29T08:20:28.215191+07:00 (UTC+07)

**PRE_FORWARD_READY / PILOT_NOT_YET_LAUNCHED** — snapshot ก่อน model calls ไม่ใช่ผล pilot. ผู้ใช้อนุมัติ implementation/CPU acceptance และ pilot0.4B≤7calls ภายใต้ SHARED_GPU_QUALITY_ONLY เท่านั้น ไม่อนุมัติ full evaluation/CPI retries/รุ่นอื่น

## ข้อกำหนดที่ปิดแล้วก่อนดู pilot scores

- Matching: geometrycanonical masks, maximize cardinalityแล้วsumIoU, canonicallexicographicoptimumภายใน1e-12; ไม่ใช้GTclass/semanticqualityเลือกคู่ Identicalgeometryใช้stablefallbackและรายงานambiguity; IDrenameinvarianceไม่อ้างทุกกรณี
- Counterexample actualCPU: stableGT-IDเดิม Q=1→0 หลังrename; revisedgeometry Q=1→1 สำหรับdistinctGTgeometry ทั้งสองassignmentsมีcardinality2/sumIoU1เท่ากัน
- C3เป็นglobalmean Hair/Upper/Lowerเท่านั้น Faceยังเป็นvalidnegative ไม่มีQ_C3/G_sem_C3. C4ยังเป็นpersonmetricหลัก; mapping/Faceproxy/garmentunions/OTHERpolicyไม่เปลี่ยน

## Implementation และ CPU acceptance ที่ทำจริง

Newpackage `src/common_view`, scripts/materialize_common_gt.py,verify_common_view_cpu.py,prepare_common_pilot.py,run_common_sapiens_pilot.py,render_common_pilot.py แยกจากnativebenchmark configs/cihp_sapiens_04b_pilot.json binds revision2 ไม่แก้frozenworker/scorer/adapters/nativeconfigs

22independentexpectedvaluecasesผ่าน actualpacket→scorer→reporter รวม tinyunion/OTHER/overlap/empty/missed/duplicate/VOID/ownerunknown/zero-denominator/geometry/IDrenaming/ties/cache/orphan/strictnull. Actualpinnedsourcepreprocessorผ่านasymmetricRGBnormalization+logit-mapback+packetfixture Savednativepackets4ระบบ×1ภาพ0021448ผ่านread-onlyintegration ไม่มีinferenceซ้ำ ดู [CPUacceptance](../runs/common-c4p-pilot-20261029T010410394659Z/CPU_ACCEPTANCE.json)

MaterializeGT-onlyครบ5,000IDs: G_loc17,520, **G_sem_C4=17,454**, ownerunknown0/VOID0; ไม่ใช่การscoring5,000predictions ไม่มีpersondenominatorC3 [GTsummary](../runs/common-c4p-pilot-20261029T010410394659Z/GT_BINDING_SUMMARY.json)

## Readiness ก่อน forward

Exact0.4BsegmentationcheckpointSHA256 b85fdb50b7d6123a967d5ee4a505e222baff8d2f7ad6bbf353578c1a61dfbac9 ตรงlocalregistry,headerhead29classes/source/config/environmentbindingsตรวจแล้ว ไม่เรียกlocalhashว่าcreator-authenticityproof. Modelstrictloadและwarmupยังต้องตรวจในpilot. Python3.12.3/PyTorch2.14.0+cu130/CUDA13.0;ใช้existing .venvs/sapiens2-pilot ไม่install/เปลี่ยนallocatorหรือenvironment

Resourcepolicy [sharedGPUamendment](../runs/common-c4p-pilot-20261029T010410394659Z/RESOURCE_POLICY.json), readiness [record](../runs/common-c4p-pilot-20261029T010410394659Z/READINESS.json). พบexternalPIDแต่ไม่เป็นblocker;ไม่แตะprocessอื่น คงFP32/batch1/noAMP/TF32/extraTTA/native1024×768stretch/native29logitmapback/frozenYOLOcache. Guard24h/80GiB/free50GiB,noautomaticOOM/modelretry/fallback. Actualmemoryfeasibilityยังไม่รับรองก่อนforward

## Pilot scope และผล

Pendinglaunch: ≤1TRAIN0000930warmupnot-scored แล้ว VAL0021448,0006909,0001538,0001413,0027897,0031248 ตามลำดับ ไม่เกิน7calls/oneattemptต่อภาพ. ตอนsnapshotนี้calls0,success0 ไม่รายงานqualityscoreล่วงหน้า. Full5,000primary=null;pilotไม่ใช่benchmarkประชากรหรือgeneralranking

Artifactsแยกprivate workspace-relative: `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/common_view/common-c4p-pilot-20261029T010410394659Z`; GTdomains/eligibility,BINDINGS.jsonl,CPUlogs,readiness/envอยู่แล้ว Canonicalnative/สองCPIพักคงเดิม ภาพdatasetไม่ขึ้นpublicGit เมื่อpilotมีผลให้อัปเดตรายงานนี้จากcanonicalRUN/packet/score/parity/closureและตรวจvisualgeometry/ownershipก่อนสรุป

Next: commitreadiness/protocol/sourceก่อนcalls→launchdedicateddetached0.4Bonly→readback6packets/saved-maskscore/QANetextentparity→reportclosure ห้ามเปิดรุ่นอื่นหรือfullvalidationจากpilotผ่าน
