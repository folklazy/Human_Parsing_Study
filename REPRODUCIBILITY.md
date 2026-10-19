# Reproducibility Boundaries

## What can be verified without account access or GPU

The released summary CSVs/JSON reports, population totals, INCOMPLETE/null policy, failure inventory, source/config copy hashes, synthetic matching/scoring/lifecycle contracts and documentation navigation can be checked on CPU using SETUP.md. The public validator does not infer missing measurements or start subprocess model workers.

## What remains external

Datasets/checkpoints, detailed GT pixel/person bindings, native framework source/builds, 5,000-row source component ledgers, lossless per-image masks/boxes, packet arrays and both 10,000-row scoring journals remain local. Their original paths, sizes/hashes where recorded, source URLs and access status are in ARTIFACTS.md / publication/EXTERNAL_ARTIFACTS.json. No artifact is claimed publicly hosted when it is not. Native parser source/revision is separate from the later first-party Git snapshot.

The server post-export validator checked source journals/reports, original protected files and six YOLO Git statuses. A clean public clone can check the published summary counterparts and recorded hashes but cannot independently re-open omitted arrays. Per-target final scores are not fabricated from aggregate CSVs. Existing generation scripts may require server-only files or refuse overwriting; they are historical implementation, not quickstart commands.

## Provenance distinctions

- Launch freeze V11 and restored V12 establish executed configuration; no Git commit existed for the study at launch.
- The first public candidate commit is an explicitly post-run snapshot. It must not be cited as the launch commit or proof of pre-registration.
- Local checkpoint SHA256 proves identity with the locally inventoried bytes; without an upstream published digest it is not cryptographic author-authenticity verification.
- Archived 151 application tests and original 67 foundation evidence are not collapsed into a new 218-test claim. Clean-checkout portable counts are recorded separately.
- Scoped continuation of never-attempted CPI images and isolated detector restoration preserve the original trial/failure evidence; neither proves general cached scoring/resume.
- Historical reports retain their original knowledge/authorization scope. Current indexes do not rewrite them.

See [publication validation](publication/CLEAN_CHECKOUT_VALIDATION.json), [source copies](publication/SOURCE_COPY_MANIFEST.json), [run provenance](cohorts/first_cpi_t3b/RUN_MANIFEST.json), [component notices](THIRD_PARTY_NOTICES.md). No GPU benchmark was rerun for publication.

Two preserved launch-plan tests check actual checkpoint/config existence and are explicitly NOT RUN by the portable suite. The first clean attempt exposed this dependency (135 tests, 2 errors); the corrected test selection runs 133 portable tests and records the two external-asset cases separately, without weakening production gates or manufacturing weights. Fresh-integration and validation-launch package suites are also external-asset tests.
