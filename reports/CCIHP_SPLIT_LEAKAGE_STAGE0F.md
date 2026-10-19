# CCIHP — Split leakage Stage 0F

## Exact evidence

JPEG-byte train–VAL groups: 39; corresponding VAL IDs: 39. This reuses prior39group evidence and cross-checks source-byte hashes while reading RGB

Decoded-RGB train–VAL groups: 39; VAL IDs: **39**. Within-VAL decoded groups: **1**, VAL IDs in these groups: **2**. Pixel hashes include width/height plus exactRGBbytes; strictPillow decoding/noEXIF transform is pinned

[Exact groups](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/EXACT_DUPLICATES.json); [GT source-map byte-identity comparison](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/DUPLICATE_GT_IDENTITY_DIAGNOSTICS.json). SameRGB≠samepersonlabels; differingPNGhashes alone do not prove different decodedGT or wrong annotation. No claim public checkpoints memorized anysample

## Proposed populations — original preserved

| Population | Images | Native GT persons |
|---|---:|---:|
| original_source_target | 5,000 | 17,548 |
| overlap_controlled_source_target | 4,961 | 17,434 |
| readable_source_view | 5,000 | 17,548 |
| overlap_controlled_readable_view | 4,961 | 17,434 |

[Exact IDs/denominators](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/VALIDATION_POPULATIONS_DRAFT.json). Primary original-source score and overlap-controlled sensitivity stay separate tables; latter removes only exact decoded TRAIN reuse, not all near reuse, VAL repetitions or unknown pretraining. No source split edits, exclusionsactivated or benchmark scores. Additional withinVAL de-duplication needs separate policy approval

## Near-duplicate risk screen

Prespecified64bit DCT pHash on32×32LANCZOSgrayscale, top8×8median includingDC; Hamming≤4 and aspect-relative difference≤5%. Five disjoint bit-block index finds all candidates within the specified hash radius without quadratic image comparisons. Screening all decoded TRAIN+VAL metadata: **114 non-exact candidate pairs** involvingVAL. Exact decoded matches excluded fromnearcount to avoid duplication

[Candidate evidence](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/NEAR_DUPLICATE_SCREEN.json). This is a reproducible risk screen, not proof of common scene or leakage; visually similar differentpeople can collide and resized/cropped/changed images may be missed. Candidates need independent inspection before any new sensitivity exclusion. No threshold/taxonomy/model selection used VAL performance
