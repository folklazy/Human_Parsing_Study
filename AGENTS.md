# Agent continuation contract

Read README.md, STUDY_STATE.json, HANDOFF.md, EXPERIMENT_PROTOCOL.md and publication/PUBLICATION_STATE.json first. This directory is a **public staging snapshot** of the separate canonical working copy `Human_Parsing_MHPv2_Study`; do not confuse them or auto-sync in either direction.

- The executed cohort is closed: FINISHED_WITH_INCOMPLETE_SYSTEMS. No new inference, retries, downloads, training, validation tuning, CCTV, hybrid, attribute study or benchmark is authorized by this repository.
- Preserve original results, null main metrics, failures, frozen config/decisions/mapping and historical reports. Do not promote CPI mapping to DIRECT_VERIFIED or use successful subsets to rank systems.
- Existing V11/V12 `full_benchmark: true` documents past scoped user approval, not permission for another run. Inventory download approvals were not benchmark approval for all variants.
- Use SETUP.md portable CPU checks first. Project-bound tests require separately supplied external assets; do not fabricate hash-bound fixtures or downgrade their gates to make a clone pass.
- Never install into the working YOLO environment, alter datasets/weights/remotes, execute old orchestrators, blindly add artifacts or create/publish a remote without authorization.
- Preserve research scope: independent noncommercial academic evaluation; Sapiens2 use restrictions are independent from historical technical runs; 5B remains excluded. No commercial/deployment permission is claimed.
- Prefer pathlib/root-relative paths. Original absolute paths in historical records are provenance, not public download URLs.
- Source changes must be reviewed/tested locally, then explicitly cherry-picked/synced to the canonical working copy by path/hash manifest. Never overwrite either working tree wholesale. Capture new source hashes and require a newly approved configuration for a new experiment.
- Current active docs, historical reports and external dependency references are indexed separately. A post-run Git commit is not the launch revision. Never force push, rewrite tags or publish old Git histories automatically.

Safe entry points: `python scripts/validate_public_repository.py` (stdlib checks) and `python scripts/run_portable_cpu_tests.py` (synthetic CPU suite only). Neither loads models or opens original datasets. Full reproduction limits are in REPRODUCIBILITY.md.
