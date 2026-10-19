# Handoff — Closed First CPI Cohort

## Current result

Two CPI CIHP native parsers plus frozen YOLO26x ran T3b FP32 over one 5,000-image reference input population; 4,961-image main is a scoring membership subset. Both systems are INCOMPLETE under STRICT_COMPLETE. Main metrics are null. Keep all 8 rows and 566 native failure/invalid records. [Report](REPORT.md), [run manifest](cohorts/first_cpi_t3b/RUN_MANIFEST.json).

## Authority and state

Current executed config [configs/application_v2_first_cohort_v12.yaml](configs/application_v2_first_cohort_v12.yaml) / decision [provenance/APPLICATION_V2_DECISIONS_V11.json](provenance/APPLICATION_V2_DECISIONS_V11.json); original [provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/FREEZE.json](provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/FREEZE.json) and restored [provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/RESTORED_PROFILE_FREEZE.json](provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/RESTORED_PROFILE_FREEZE.json). Source hashes, actual environment strings and scope take precedence over a latest-number filename or stale prose. Mapping remains ACCEPTED_WITH_INDIRECT_EVIDENCE. The full roster/inventory is separate.

## First actions for another person/agent

1. Run the stdlib public validator; inspect STUDY_STATE.json and the canonical CSVs.
2. Follow SETUP.md for tested portable CPU fixtures. Do not execute first_cohort_entrypoint/restore/native workers as setup.
3. Read the explicit external artifact inventory. No public dataset/weight/prediction mirror exists; request authorized local access or independently acquire matching upstream bytes subject to terms.
4. Read reports/HISTORY_INDEX.md to separate superseded Stage 0 proposals from accepted cohort policies and terminal execution evidence.

## Outstanding work

The experiments did not establish a quality winner. OOM correction and interrupted-image handling in any future run need a new, reviewable execution revision, with TRAIN-only engineering and frozen population/scoring rules before any new VAL pass. Do not retroactively retry or fill the present main scores. No need to reopen the accepted five policies or the closed channel-header search absent concrete new contradictions.

Clean cloning does not provide native CUDA builds, all annotation bindings or semantic visual case assets. Public image redistribution is not cleared. Licensing remains component-specific; deployment is outside research scope. Repository publication is pending the single public-approval gate; an agent outside the account has not been tested.

## Working-copy synchronization

Canonical editable research remains the sibling `Human_Parsing_MHPv2_Study` (not Git-initialized at snapshot). This candidate is `Human_Parsing_Study_Public`. Source copies preserve bytes and original hashes in publication/SOURCE_COPY_MANIFEST.json. No files are moved/deleted. Changes in this staging copy do not automatically reach the canonical study; review explicit diffs and before/after hashes before a future authorized sync.
