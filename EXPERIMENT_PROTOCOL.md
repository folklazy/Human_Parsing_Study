# First CPI T3b Cohort — Executed Protocol

Run `first-cohort-benchmark-20261016T094257313856Z`. Source of executable values: [V12 config](configs/application_v2_first_cohort_v12.yaml) / [Decision V11](provenance/APPLICATION_V2_DECISIONS_V11.json); original [V11 launch freeze](provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/FREEZE.json), [restored-profile freeze](provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/RESTORED_PROFILE_FREEZE.json). V12 retains the accepted scientific values and resolves a pre-model shared-detector environment failure; it does not alter native CPI settings.

| Item | Executed setting |
|---|---|
| Systems | CPI_R50_CIHP; CPI_ConvNeXtB_CIHP |
| Person dependency | Frozen YOLO26x-Seg |
| Track / precision | T3b / FP32, autocast=False, TF32=False |
| RGB | Existing CIHP DatasetNinja TAR images, byte/decode hashes and original dimensions verified |
| GT | CCIHP released Category_ids + Human_ids + Instance_ids, original grid |
| Inference population | Reference Validation 5,000 ordered IDs, once per component |
| Reports | Main 4,961 and reference 5,000, separate population bindings |
| YOLO | imgsz=640; conf=0.25; NMS IoU=0.70; max_det=200; retina_masks=True |
| Native CPI score thresholds | R50=0.01; ConvNeXt-B=0.05 |
| Association | Predicted YOLO bbox ↔ native parser bbox; IoU ≥0.50; no GT |
| Final GT matching | Native parser bbox ↔ eligible GT localization bbox; IoU ≥0.50 primary / ≥0.75 secondary |
| Assignment | One-to-one, eligible cardinality then IoU; immutable IDs then pinned SciPy tie behavior |
| Coordinates | Original image, XYXY half-open; conditioning bbox distinct from evaluation bbox |
| Target / domain | Six-foreground CPI-only mapping; released-annotation-relative GT domain |
| Completeness | STRICT_COMPLETE; no failed-image retries or score-dependent exclusions |
| Resource claims | Quality-only; no clean repeated timing or cost rankings |

Native CPI runs full frames using its released architecture/internal detector; it is not cropped or silently stripped of detection overhead. The final T3b persons are prediction-only associated to YOLO opportunities. Native unmatched instances and opportunity identities are retained as provenance; final GT matching happens after that association.

RGB/GT and source hashes are checked independently. Native outputs are lossless masks/boxes. The same inference artifacts support two report populations only against their exact matching-view/context bindings.

## Execution deviations retained as evidence

The first YOLO worker aborted before model import/image inference when config validation imported unavailable SciPy in the YOLO environment. The approved scientific settings were preserved; CPU authorization was separated from the detector bootstrap without modifying packages. YOLO then completed 5,000 images once.

R50 completed 4,475 and failed 525 CUDA-OOM images. ConvNeXt-B initially committed 3,779 rows; image 0034896 had an incomplete NPZ and remains INVALID/UNRESOLVED_INTERRUPTION. Exactly 1,220 never-attempted images continued with unchanged settings, yielding a combined 4,959 complete / 40 OOM / 1 invalid. Original ledgers and partial bytes remain external and unmodified. This is not a retry of failed images.

## Evidence and reproduction limits

[Technical results](REPORT.md), [population manifest](cohorts/first_cpi_t3b/POPULATIONS.json), [data contract](DATA_SCHEMA.md), [external dependencies](ARTIFACTS.md). The archived settings include legacy preparation fields; the historical validation execution uses `first_cohort.execution_spec` and `validation_launch`, not the old 20-variant inventory or bounded-TRAIN roster. Do not infer permission from a historical full_benchmark flag or relaunch an old orchestrator.
