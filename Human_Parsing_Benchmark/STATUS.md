# Human Parsing Benchmark — current status

Updated: 2026-10-28T22:32:24.395816+07:00 (Asia/Bangkok)

**RPR_CIHP_ROUND_BLOCKED — EXTERNAL_GPU_BUSY**. Latest user authorizes only RP-R-CNN CIHP on frozen nativeCIHP VAL5000; stop before CPI. Resource snapshot22:30:14+07:00 shows external compute PID126277 using1736MiB onTeslaT4. Native policy rejects any existing compute PID; utilization0%/free13173MiB is not sufficient. No Human Parsing worker/controller was active. No new worker/controller/session, GPU smoke, inference, retry, waiting/poll loop or other-process intervention was performed.

Existing/reused RPR VAL results0; remaining5000 IDs. Failed/invalid VAL0, not_attempted5000, main score null (STRICT_COMPLETE). Prior EXTERNAL_GPU_BUSY setup record preserved; it is not a VAL inference failure. D2FP/QANet/M2FP results untouched.

[RP-R-CNN report section](reports/CIHP_CONTROLLED_CONTINUATION.md) / [preflight evidence](runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-preflight-20261028T153224395816Z/PREFLIGHT.json) / [PLAN](PLAN.md). Round `rpr-cihp-preflight-20261028T153224395816Z`, parent `cihp-native-six-20261028T034103254470Z`; execution segment NOT_LAUNCHED. Frozen config/source/native-config/source-commit bindings checked; checkpoint size/existence checked, payload rehash and environment/model startup deferred because resource gate failed.

Next: end this blocked round. On later continuation, recheck GPU once, proceed within RPR-only authorization if policy passes, otherwise report BLOCKED without polling. Do not launch broad historical controller or CPI, matrix, Sapiens2, color, training/CCTV. No precision/resource/protocol changes.
