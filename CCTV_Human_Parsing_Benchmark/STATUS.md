# CCTV parsing — current status

Updated 2026-11-01T09:14:13.866643+07:00 (Asia/Bangkok). **SELECTED_PART_EVALUATION_COMPLETE —9/9×90IDs**, no active model worker or CPU scorer.

[Final Thai report](reports/CCTV_SELECTED_PART_RESULTS_TH.md) → [Protocol](SELECTED_PART_PROTOCOL.md) → [Evidence](reports/SELECTED_PART_EVALUATION_EVIDENCE.json). Observed selected-task leader: **QANet**, macro mean selected-part IoU4 61.773%, Dice4 69.203%. Primary315parts; all324 sensitivity reported. GT-only agent screening is not independent expert certification; no full-scene/deployment claim.

Original partial/native packets/GT/config/recall results unchanged; old known-domain IoU report remains historical diagnostic. New evaluation uses whole selected-person masks with spill FP and retained misses. Model inference calls0; no retries/training/environment changes.

Next: review this final report and QANet configuration proposal. Full-scene metrics/production acceptance require separate annotation scope/QA and independent confirmation; no new experiment scheduled automatically. Private review/gallery/records stay in outputs; public Git has aggregates only.

## Sapiens input audit

[Preprocessing audit](reports/SAPIENS2_PREPROCESSING_AUDIT_TH.md):12CPUinputtensorcases across3segconfigs exactlymatchofficialdemo/directnormalization. NoRGB/BGR/doublenormalizationbugfoundonthesecases. Full-frame1920×1080→768×1024stretchstronglychangespersonaspect/scale;qualityeffectunproven. No learnedforward/checkpointload/GPUworker or scorechanges. Nextboundedreferenceforwardwouldrequireanewinferencescope; existing9/9resultsremainconfiguration-specific.
