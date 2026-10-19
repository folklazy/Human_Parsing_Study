# MHP-v2 Dataset Audit — Stage 0A

**DATASET_BLOCKED.** Structure and per-person decoding are established; four required RGB images cannot be decoded, exact cross-split content reuse is confirmed, and a selected GT ownership anomaly needs review. No source file was repaired, excluded from the original split or rewritten. No parser inference was performed.

## Dataset identification and inventory

Canonical physical root: `datasets/LV-MHP-v2/` relative to the workspace. Local README identifies **LV MHP v2.0**; its structure/labels/counts agree with the [official project](https://lv-mhp.github.io/) and [official implementation](https://github.com/ZhaoJ9014/Multi-Human-Parsing). The project permits noncommercial research subject to its license terms; this does not establish commercial/deployment permission.

The earlier import record names a 5,429,618,040-byte ZIP with SHA256 `89f010742d4797d3efd7a7eab83a405d9828749381da20638a03df947238059e` and reports CRC-validated extraction. That ZIP no longer exists at the recorded local path. Its original download URL and equivalence to an independently downloaded official archive were **not verified** here. Do not treat the import record as an authoritative official-release hash.

| Split | Images on disk / original list | Per-person PNGs | Pose MAT files | Fully decoded RGB |
|---|---:|---:|---:|---:|
| Train | 15,403 / 15,403 | 41,056 | 15,403 | 15,400 |
| Validation | 5,000 / 5,000 | 13,260 | 5,000 | 4,999 |
| Test | 5,000 / 5,000 | 0 supplied | 0 supplied | 5,000 |
| Total | 25,403 | 54,316 | 20,403 | 25,399 |

**100,134 local files** were SHA256-hashed, including non-training metadata. No missing/orphan required image or parsing files, duplicate split IDs, filename-declared person-count mismatch, invalid parsing person ID, empty parsing plane, invalid first-channel class or GT/image-header dimension mismatch was found. Original train/val/test IDs are disjoint. Auxiliary test-interaction lists contain 500/1,000 IDs and must remain subsets of test. Test GT absence is expected.

The initial decoder exception skipped annotations behind four unreadable RGBs. Its index/report/script revision are archived. A supplementary read-only pass independently decoded the remaining **16 PNGs** and their pose files, producing a V2 GT index: **all 54,316 person planes** now pass decoding, native-ID/dimension checks and lossless PNG round trip. RGB failure remains a blocker. [Manifest](../manifests/DATASET_MANIFEST.json), [integrity record](../provenance/DATASET_INTEGRITY.json).

## Required RGB failures

| Split | Image ID | PIL strict result | OpenCV 4.11 tolerant attempt |
|---|---|---|---|
| Train | 1396 | Truncated JPEG, 21 bytes unprocessed | No decoded image |
| Train | 18613 | Truncated JPEG, 0 bytes unprocessed | No decoded image |
| Train | 24328 | Truncated JPEG, 19 bytes unprocessed | No decoded image |
| Validation | 17844 | Truncated JPEG, 26 bytes unprocessed | No decoded image |

All four lack the JPEG EOI marker. Header dimensions and GT are readable; complete original RGB pixels are not verified. No forced permissive PIL decode, marker insertion, label repair or split exclusion was adopted. The evidence contains exact source SHA256 values in `TRUNCATED_JPEG_DIAGNOSTIC.json` under the active run. A verified replacement source or explicitly approved non-destructive evaluation policy is needed.

## Annotation representation and identity

The official v2 evaluator explicitly reads the first PNG channel. Locally, **54,315 masks are RGBA and one is indexed P**; for RGBA, semantic indices are in the first channel, not rendered grayscale. Alpha 255 is not ignore. Background is 0, foreground IDs 1–58; no additional native semantic ID or documented native void was found. Adapter training padding may use 255 separately.

One file is the documented person annotation unit: `imageID_totalPersons_personFileID.png`. Canonical identity is `imageID:parsing:personFileID`, with source path/hash and original-coordinate plane preserved. Separate planes retain overlap. Full parsing foreground contains body/clothes plus associated/carried objects; it is not an anatomical silhouette. A draft body/clothing localization subset is stored separately and never replaces native parsing truth.

Pose entries use separate `person_0…` keys and 20×3 native arrays. Numeric matching to parsing suffixes is invalid: in image 1004 the order differs substantially. **517 images have pose/parsing count differences** among the regular decoded-image records. Pose records behind the four RGB failures were separately read; no extra mismatch was inferred. Additional optional warnings include single-person parsing examples despite the paper's 2–26 headline and pose shape/metadata variation. None was silently changed. This does not block reading parsing files, but it blocks any assumed pose-to-parsing identity join.

## Integrity is not semantic correctness

![Selected ownership anomaly](../outputs/visualizations/stage0-20261008T063349Z/mhpv2_gt/instance_ownership_9968.png)

In `train/9968`, native parsing file `9968_02_01.png` visibly labels face/garment regions at both adults, while `9968_02_02.png` substantially overlaps the male's support. **Observation:** source planes contain these regions. **Interpretation:** the selected file's physical-person ownership is questionable beyond ordinary boundary overlap; it needs author/source verification. The reader preserves the original error/ambiguity faithfully. No dataset-wide owner-error count is established, and other overlapping masks are not automatically called corrupt. [Ownership evidence](../provenance/GT_INSTANCE_OWNERSHIP_ANOMALY.json).

This separates verified per-file identity/decoding from unverified annotation ownership. The study cannot claim that every canonical plane is a perfectly labeled physical person merely because lossless conversion passes.

## Exact duplicates and leakage

Decoded RGB hashes include original dimensions. There are **2,267 exact duplicate groups**, of which **1,357 span splits**. Of these, 595 involve train/val only, 552 train/test only, 177 val/test only and 33 all three. Including three-way groups, **628 train/val groups contain 652 validation IDs with exact training content**. Byte-identical JPEG examples were independently confirmed, including train 216 / val 18678 and train 218 / val 18696.

Original membership stays unchanged in [FINAL_VALIDATION_SET.json](../manifests/FINAL_VALIDATION_SET.json). [LEAKAGE_AUDIT.json](../manifests/LEAKAGE_AUDIT.json) is an evidence list, not a replacement split. MHP-trained checkpoints may already have seen identical validation content through train; their exact sample-level exposure has not been inspected. Do not describe the official validation set as content-independent. Near-duplicate/external-dataset reuse has not been exhaustively checked. No threshold/model selection used validation scores.

## Statistics and diagnostic selection

Statistics are **GT-derived**, not model results. Train parsing counts range 1–26; validation includes a few one-person examples and ranges up to 18. Native per-person median foreground areas are recorded in the manifest; full distributions of image resolutions, foreground area, bbox sizes/aspect ratio, image-area fraction and bbox occupancy are reproducible in [person statistics](../metrics/DATASET_PERSON_STATISTICS.csv). Background/support is counted per person plane, with overlap retained, not once per scene.

Native class frequencies/support are in [class support](../metrics/DATASET_NATIVE_CLASS_SUPPORT.csv). Rare person-plane occurrences include Umbrella 82, Bats 138 and Cases 261. Native labels do not prove visually correct fine-class assignment in every sample.

Observed overlapping **annotation support** is separately recorded across all planes; it must not be labeled an occlusion-severity statistic. Ownership anomalies and carried objects can also contribute. These statistics do not establish CCTV robustness.

![Eight deterministic training diagnostics](../outputs/visualizations/stage0-20261008T063349Z/mhpv2_gt/contact_sheet.png)

Eight train-only examples cover a fixed ordinary image, 26-person scene, maximum support overlap, a small baby-face-only instance, largest-area person and three rare labels. Original RGB, display-only person identities, selected native plane and canonical lossless plane are shown. The native/canonical panels are identical by construction and tested pixelwise; that demonstrates conversion fidelity, not independent GT correctness. Overlap is magenta only for visualization, with every source plane retained.

The [development manifest](../manifests/DEVELOPMENT_SET.json) is a blocked draft selected from readable train images using seed 20261008 and documented GT variation. It does not change train membership or authorize model execution. Timing manifests are fixed draft train workloads, not timings. No validation image was used for qualitative/protocol tuning.

## Recommendation

Keep the audit gate **DATASET_BLOCKED**. Obtain verifiable RGB replacements or an approved source-preserving failure policy; review the native ownership anomaly; settle content-overlap reporting and checkpoint exposure before a Stage 1 freeze. No PPSS clarification is needed for this gate. Original datasets remain unchanged.
