# External Artifacts and Access

Git contains first-party code/tests, exact frozen configs/decisions/mappings, reports, machine-readable summary results, small factual manifests and publication-generated plots. It contains no dataset RGB/GT pixels, weights, environment binaries, bulk predictions/logits or company CCTV. Source dataset photos/overlays are withheld because public redistribution rights have not been established for the selected images. No broad image/CSV/JSON ignore pattern hides essential summaries.

| External artifact | Recorded bytes | SHA256 / access |
|---|---:|---|
| datasets/CCIHP_icip.zip | 842,868,844 | 373f3183bf58c3e5637ba3564c9b8abef923dc434b78f469b3722282d1514829; user-transferred, no public mirror created |
| datasets/cihp-DatasetNinja.tar | 2,015,375,360 | 085d2b694a8c4e0081292a905972e1f31af9d454c12698427b187c7af67a2793; source project [DatasetNinja CIHP](https://datasetninja.com/cihp) |
| datasets/LV-MHP-v2.zip | See original import | 89f010742d4797d3efd7a7eab83a405d9828749381da20638a03df947238059e; [original MHP project](https://lv-mhp.github.io/) |
| models/yolo26x-seg.pt | See source checkpoint provenance | 92b3de0065766a17180d6219858717dc9d03cdce8a3ca9576c97fd75aabb64f3; frozen upstream dependency |
| CPI_R50_CIHP / CPI_ConvNeXtB_CIHP | 571,901,148 / 1,301,413,296 | Hashes, official source URLs and license notes in [inventory](inventory/MODEL_INVENTORY.csv) |
| GT context bindings, component ledgers, per-image arrays, scoring journals | Per-item metadata where available | [External manifest](publication/EXTERNAL_ARTIFACTS.json); local custodian access only, no signed/restricted URL exposed |

Public upstream source links are not a promise that weights/datasets are currently anonymously downloadable. Exact acquisition must respect current source terms and applicable user authorization. Dataset rights, annotation rights, code, checkpoints and dependencies remain separate. No new acquisition was performed for this publication.

## Reconstructing a full local view

Obtain permitted matching external assets, verify their sizes and recorded hashes, preserve original read-only datasets, and recreate required native environments from inspected version/source records. Restore detailed GT packages and original run-owned outputs at their recorded relative paths before running project-bound validators. Unknown or unavailable assets remain unavailable; do not substitute approximate GT, default checkpoints or guessed channel mappings. A new model execution still requires approval.

The working copy remains `Human_Parsing_MHPv2_Study` next to this public staging copy. Local paths in retained evidence describe that workspace, not Internet endpoints. Some older records reference pilot experiments outside this repository; those dependencies are not automatically redistributed or declared reproducible from a clone.

The four original aggregate JSON reports (~7.7 MB each) contain bulk operational ledgers and remain external. Compact derived views are released at `cohorts/first_cpi_t3b/reports/`, with source/public hashes in `publication/PUBLIC_REPORT_VIEWS.json`.
