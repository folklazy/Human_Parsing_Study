# Human Parsing Benchmark — current status

Updated 2026-10-29T13:37:34.226601+07:00 Bangkok UTC+07

**COMMON_C4P_FULL_RUNNING / FIRST_NEW_PACKET_PASS**

[Full report and five-system status](reports/CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md) · [full config](configs/cihp_sapiens_c4p_full.json) · [freeze](runs/common-c4p-full-20261029T063458522990Z/FREEZE.json)

- Approved: saved-only QANet/M2FP/D2FP/RP-R-CNN + Sapiens2 segmentation0.4B official CIHP VAL5,000. Stop afterwards. No CPI launched by this common batch; a later separate user-authorized CPI ConvNeXt manual attempt is recorded below. No0.8B/1B/newYOLO/training/color/CCTV.
- Native results/pilot core/protocol preserved. Same C4-P revision2 mapping/ties/C3global/OTHER/VOID. G_loc17,520/G_sem_C417,454 verified from exact GT manifest, not hardcoded scorer denominators.
- Pilot6 reuse compatibility PASS; pending4,994, new process≤1TRAINwarmup, no automatic retry/fallback. New full approval is separate from consumed pilot allowance.
- PNGoriginal6/6 match oldmanifest; four chat-copy mismatches reported, copiedbytes not available for independent checking; no cause inferred. Packet checks separate.
- CPU7fixturesPASS;8savedlegacyintegrations+6pilotpacketsPASS. Projected-confusion/pixel equivalence and full-person scorer equivalence to frozen revision2 confirmed. No new model calls before launch.
- Storage estimate21.673GiB includes arrays/metadata/logs/temp/headroom;80GiB stream/free50GiB/24h retained. Pilot operations accounted. Planning200GiB not global cap/proven total. Shared-GPU diagnostics, no speed ranking.

Run `common-c4p-full-20261029T063458522990Z`. New artifacts `Human_Parsing_Benchmark/outputs/common_view/common-c4p-full-20261029T063458522990Z`, historical artifacts unchanged.

```bash
.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/common_full_progress.py --watch
```

Launch 2026-10-29T13:43:06.533541+07:00 check: controllerPID380379/SID380379,GPUworkerPID380414;launchcommit`b64eeb98128f9178ac5556d302c1efd8e92dad64`. Firstnewpacket0000001COMMIT/native29/geometry/ownership/saved-scorePASS. ObservedGPUcomplete45/5000(reused6);CPUstates recorded in [first packet check](runs/common-c4p-full-20261029T063458522990Z/FIRST_PACKET_CHECK.json).

Next: detached batch continues without chat; use progress viewer/state for current counts. One GPU worker plus one sequential saved-only CPU process. No continuous Codex polling, no protocol changes, no next model/retry. Automatic Thai report and per-system Git updates then terminal closure; primary remains null per incomplete system.

## Later explicit CPI ConvNeXt attempt — 2026-10-29T14:09:52.447523+07:00

Userapprovedconcurrentmanualattempt,now **STOPPED_INCOMPLETE**. Reuse113+new32=145/5000,failed1/invalid0,missing4855,mainnull. OOM0001641 (request4.10GiB/free1.67GiB);noautomaticretry. BothPIDs401349/401656exited. [Thai closure](reports/convnext-20261029T070405365918Z.md). OriginalSapiens0.4B/commonCPUcontinuewithoutscientificchanges;usecommonprogressforlivecounts. NoR50/otherSapienssize.
