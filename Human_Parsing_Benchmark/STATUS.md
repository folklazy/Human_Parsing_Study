# Human Parsing Benchmark — current status

Updated **2026-10-29T08:20:28.215191+07:00 Bangkok (UTC+07)**

**COMMON_VIEW_CPU_ACCEPTANCE_PASS / PRE_FORWARD_READY / AUTHORIZED_PILOT_ONLY**

- [Current implementation/pilot report](reports/CIHP_SAPIENS_04B_PILOT_TH.md); [protocol](reports/CIHP_SAPIENS_COMMON_VIEW_PROTOCOL_TH.md), [revision2](protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json)
- CPU22expected-valuecases PASS +4savednativepackets×1frame integration PASS; no newmodelcalls yet. Tiesgeometrycanonicalwithambiguityfallback, C3globalonly/noQ_C3
- GT-onlyC4bindings5,000 complete: G_loc17,520,G_sem_C4=17,454; nofullcommonscoring. SourceGTunchanged
- Sapiens2_0.4b conditional≤7calls pilot explicitlyauthorized SHARED_GPU_QUALITY_ONLY. Readinesspre-forwardPASS;strictload/warmupnext;noPID-onlyblock
- Four native systems COMPLETE5,000each; CPIbothPAUSED_NOT_CANCELLED,3/113successes/history/STRICT_COMPLETEmainnull unchanged
- No0.8B/1B/full5,000commonbenchmark/training/color/CCTV/newYOLOinference authorized

Run `common-c4p-pilot-20261029T010410394659Z`; rawartifacts `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/common_view/common-c4p-pilot-20261029T010410394659Z`. Next: scoped0.4Bpilotonlyaftercommittedreadiness, thenclosure/report; oldcontrollersmustnotrestart
