# CIHP native archive — import receipt

Work unit: `cihp-native-intake-20261028T030159730335Z` · Completed: 2026-10-28T03:07:13.213756+00:00

User authorized transfer/extraction of `instance-level_human_parsing.tar.gz`. Existing dataset assets and historical benchmark outputs were preserved. This is an archive intake receipt, not a full CIHP quality audit or a dataset-role/protocol decision.

- Archive: `datasets/instance-level_human_parsing.tar.gz`, retained; 2,033,753,964 bytes.
- SHA256: `6dea91e6c7ffa48c023eb0bdaa3ee259fe0d4e9d89e108bd26b312fdf646d2bb` (local received-file identity, no publisher digest/source authentication).
- Full gzip trailer CRC/ISIZE and TAR header stream: PASS. Unsafe/special members:0; duplicate normalized paths:0. TAR has no per-file CRC.
- New dataset root: `datasets/CIHP/`.
- Extracted 237,965 files / 2,078,741,021 payload bytes, counts match archive.
- Removed only wrapper `instance-level_human_parsing/` on extraction; all child paths and file bytes preserved. Fresh staging directory atomically renamed to CIHP after completion; no old dataset overwritten.

| Split | RGB files | Category_ids | Human_ids | Instance_ids |
|---|---:|---:|---:|---:|
| Training | 28,280 | 28280 | 28280 | 28280 |
| Validation | 5,000 | 5000 | 5000 | 5000 |
| Testing | 5,000 | not present | not present | not present |

Train/validation annotation basenames match RGB basenames for all six label/visualization directories (filename-level correspondence only). Testing contains RGB and split list, without corresponding annotation directories in this archive; absence alone is not diagnosed as corruption.

Archive README identifies Category_ids/Human_ids/Instance_ids as labels, and Categories/Human/Instances as rendered visualizations. Its semantic list includes19 foreground classes (Dress6), not CCIHP FaceMask6. No GT projection or taxonomy acceptance is changed by this observation.

## Evidence / limits

Compact [import manifest](../manifests/CIHP_NATIVE_IMPORT.json) records exact paths, counts and inventory hashes. Full member and per-file SHA256 inventories remain external to Git under `Human_Parsing_MHPv2_Study/outputs/dataset_intake/` with this work-unit ID. Per-file digests were calculated from member bytes streamed to closed output files; no independent second full disk read was claimed.

No full strict RGB/PNG decoding, class-value/dimension/ownership/alignment/leakage quality audit has run for this newly supplied native distribution. Original download source and publisher digest were not supplied; README does not itself establish licensing. Existing CCIHP and DatasetNinja assets remain separate. Current selection/protocol decisions remain pending; this does not start Stage B, inference or benchmark and does not review/accept the user's newly uploaded plan.

Next: locate/review the newly submitted plan under its separately requested scope; use this dataset import identity when proposing any subsequent native-CIHP audit. No automatic evaluation or dataset-role promotion.
