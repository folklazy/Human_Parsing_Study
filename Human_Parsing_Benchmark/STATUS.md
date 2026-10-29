# Human Parsing Benchmark — current status

Updated 2026-10-29T13:37:34.226601+07:00 Bangkok UTC+07

**COMMON_C4P_FULL_USER_AUTHORIZED_FROZEN / LAUNCH_PENDING**

[Full report and five-system status](reports/CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md) · [full config](configs/cihp_sapiens_c4p_full.json) · [freeze](runs/common-c4p-full-20261029T063458522990Z/FREEZE.json)

- Approved: saved-only QANet/M2FP/D2FP/RP-R-CNN + Sapiens2 segmentation0.4B official CIHP VAL5,000. Stop afterwards. No CPI/0.8B/1B/newYOLO/training/color/CCTV.
- Native results/pilot core/protocol preserved. Same C4-P revision2 mapping/ties/C3global/OTHER/VOID. G_loc17,520/G_sem_C417,454 verified from exact GT manifest, not hardcoded scorer denominators.
- Pilot6 reuse compatibility PASS; pending4,994, new process≤1TRAINwarmup, no automatic retry/fallback. New full approval is separate from consumed pilot allowance.
- PNGoriginal6/6 match oldmanifest; four chat-copy mismatches reported, copiedbytes not available for independent checking; no cause inferred. Packet checks separate.
- CPU7fixturesPASS;8savedlegacyintegrations+6pilotpacketsPASS. Projected-confusion/pixel equivalence and full-person scorer equivalence to frozen revision2 confirmed. No new model calls before launch.
- Storage estimate21.673GiB includes arrays/metadata/logs/temp/headroom;80GiB stream/free50GiB/24h retained. Pilot operations accounted. Planning200GiB not global cap/proven total. Shared-GPU diagnostics, no speed ranking.

Run `common-c4p-full-20261029T063458522990Z`. New artifacts `Human_Parsing_Benchmark/outputs/common_view/common-c4p-full-20261029T063458522990Z`, historical artifacts unchanged.

```bash
.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/common_full_progress.py --watch
```

Next: commit/pushfreeze,detachedcontroller,verifyfirstnewpacketthenreturn. One GPU worker plus one sequential saved-only CPU process after first new packet; per-system STRICT_COMPLETE, no automatic next model.
