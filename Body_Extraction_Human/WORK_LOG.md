# Application work log

## 2026-11-01 UTC / 2026-11-02 Asia/Bangkok — implement and verify first application

User requested an actual Thai web application, not a UI mockup: image/video
upload → YOLO → parsing → original-RGB clothing colors → persistent DB → AND
search and exact person/time navigation. Read workspace rules, actual model/color
selection records, existing adapters/environments and hardware/process state.
Tesla T4 present, free14,912MiB at intake; selected weights already local. No
checkpoint/data downloads or modifications to working model environments.

Created independent root-level Body_Extraction_Human. React/TS frontend; FastAPI
API; new isolated API environment; app-only PostgreSQL15 Docker container/volume;
separate durable worker with lease reconciliation/advisory lock; atomic frame
directories/DB transactions, immutable attempts, explicit cancellation/manual
retry/deletion; authenticated private storage and search. Reuse existing model
environments through IPC. Preserve all scientific results and artifacts.

Disclosed concrete Sapiens2 license clause; user explicitly requested retaining
Sapiens2 for this work. Source terms remain documented; no additional use rights
or model redistribution are claimed. QANet remains explicit alternative only.
Selected T4 MLP artifact is reused. Its CIHP garment-category requirements are
not silently filled from Sapiens generic classes: evaluate category hypotheses
and return null when they disagree. Familiar-name LAB/HSV palette is separate,
with measured fractions and no calibrated-confidence claim.

Actual first four new inputs (research-image transformations, blank, new H.264
MP4) succeeded:6frames/10persons, including no-person success and seven unknown
garment observations. AND search/deep-link checks3. No saved predictions used.
Real service/database restart preserved10persons. Deliberately missing this
app's own uploaded file produced failure; restore/manual retry succeeded in a
fresh attempt with no duplicate current frame; queued cancel/deletion/range
checks passed. All original datasets/files remained unchanged.

Chromium exercised real UI login/preview/result/person/search/refresh/video seek.
Visually inspected actual result screenshot and corrected missing Thai fonts by
bundling Noto Sans Thai through fontsource with OFL notice; corrected overlay
legend and preview validation. Eight targeted CPU/security/lease tests passed.
Initial multipart receive limit produced400 for chunked oversize; fixed response
classification to413 without relaxing the limit, then all cases passed.

Final execution-source check performed two more actual image uploads/four ROIs,
confirmed Tesla T4, exact selected source/checkpoint bindings and detector/parser
process reuse. Private attempt/source hashes remain available. No scientific
benchmark was rerun; no model accuracy or speed claim is inferred from app QA.

Deliver source/docs/config/aggregate verification only. Private files, screenshots,
credentials, DB, weights, environments and per-person records stay external to Git.
Source working tree and public publication checkout remain distinct. Publish via
the existing repository's working branch, without merging or modifying frozen
YOLO/CPI results. Next user verification with authorized new files; no automatic
new experiments or public hosting.

## 2026-11-01T19:30:00.444100+00:00 UTC — delivery closure

Final browser submission actually uploaded a new blank image through the UI, received a job, ran the worker and displayed successful zero-person output. Corrupt image preview blocked submission. Video frame selection/seek1s/2s passed; no JavaScript errors. All14actual person crops/native masks checked in original coordinates; native/clip ownership and source pixels agree. Final source hashes and selected model identities matched the two-upload T4 execution check. Existing five protected benchmark result/protocol hashes unchanged. API/worker remain detached on loopback8038; authenticated use only. Publish explicit source/docs/config/aggregate evidence to existing repository working branch; no private artifacts/secrets/model weights/Git histories.
