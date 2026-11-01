# Model identity records versus effective application configuration

`MODEL_BINDINGS.json` preserves selected entries from the existing accepted
registry, including their **historical** `route`, `current_status`, phase and file
stat fields. Those fields are not current application readiness or routing.
They are retained as origin evidence; file stat alone is not authenticity.

The effective application contract is `backend/app/settings.py:config_snapshot()`:
CONTROLLED_YOLO_PERSON_ROI, FP32, selected Sapiens2_1b, detector-mask ownership,
the explicitly recorded crop/normalization/map-back and color category policy.
It is frozen into each job and checked against the worker at execution. The
inference host selects exact model ID/checkpoint/config/source identities, not
the historical registry's route/status. Current outcome comes from DB attempts
and artifact/provenance checks, not a similarly named registry field.

In particular the inherited Sapiens `SAPIENS_FRAME_YOLO_MASK_OWNERSHIP` field
describes an earlier study route. This application's actual inference is a person
crop. It is not renamed silently into full-frame inference. An optional QANet
native config still lives in the historical MHPv2 study; it is read only, not the
application workspace or an instruction to resume that experiment.
