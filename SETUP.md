# Setup and Safe Checks

## Portable CPU checks

Use Python 3.10+ (tested interpreter is recorded in publication validation). Create a fresh environment outside datasets/model trees if needed; installation is optional and subject to your environment policy:

```bash
python3 -m venv ../human-parsing-cpu
../human-parsing-cpu/bin/python -m pip install -r requirements-cpu.txt
../human-parsing-cpu/bin/python scripts/validate_public_repository.py
../human-parsing-cpu/bin/python scripts/run_portable_cpu_tests.py
```

No installation was performed merely for publication. The clean-checkout test uses the already available, compatible audit Python. The portable runner explicitly selects synthetic/config CPU modules that require no datasets/weights. Other retained tests are project-bound, not silently skipped as passing. Historical validation-package tests require external detailed GT bindings and their exact hashes. [Validation evidence](publication/CLEAN_CHECKOUT_VALIDATION.json) gives actual counts/versions; old server **151 tests** are separate evidence, not the clean-checkout count.

## Native execution environment (historical, not install/run authorization)

The executed native CPI worker used isolated parser-legacy-cu113; YOLO used the existing YOLO environment; CPU scoring used mhpv2-stage0. See [environment table](env_specs/EXECUTED_ENVIRONMENTS.csv) for actual Python/Torch/CUDA/GPU strings extracted from run manifests, and [CPU pins](requirements-cpu.txt). Do not install old MMDetection/MMCV/CUDA dependencies into the YOLO environment or change driver/system CUDA.

Third-party code, extensions, checkpoint bytes, dataset archives, detailed GT packages and native output arrays are absent from Git. Versions alone are not a complete native dependency lock. Historic environment freezes/source/config hashes are retained where available; no fresh native compatibility claim is made here. Source repositories/revisions and required patches are in THIRD_PARTY_NOTICES.md and ARTIFACTS.md.

## Executed artifacts

Place authorized external resources at the workspace-relative locations referenced by the unchanged frozen config, or propose a separately validated relocation/config revision. Never silently change path-bearing historical records or hash-bound configs. No single clone-and-run command can reproduce the full benchmark from this repository alone.

Two preserved launch-plan tests check actual checkpoint/config existence and are explicitly NOT RUN by the portable suite. The first clean attempt exposed this dependency (135 tests, 2 errors); the corrected test selection runs 133 portable tests and records the two external-asset cases separately, without weakening production gates or manufacturing weights. Fresh-integration and validation-launch package suites are also external-asset tests.
