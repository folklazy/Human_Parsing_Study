# Reproducibility — Executed Stage 0

Run: `stage0-20261008T063349Z`. Root paths derive from scripts/workspace; no original dataset/environment path is relocated. Source trees, checkpoints and environments are external assets. The study directory is not Git-initialized; no remote/commit/push was created. Original six YOLO repositories have before/after HEAD/status/hash evidence; existing untracked work is preserved.

Actual audit/test commands:

```bash
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
  ../.venvs/mhpv2-stage0/bin/python scripts/audit_mhpv2.py --workers 3
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
  ../.venvs/mhpv2-stage0/bin/python scripts/complete_mhpv2_audit.py
PYTHONDONTWRITEBYTECODE=1 ../.venvs/mhpv2-stage0/bin/python \
  -m unittest discover -s tests -p 'test_mhpv2_stage0.py' -v
PYTHONDONTWRITEBYTECODE=1 ../.venvs/mhpv2-stage0/bin/python scripts/test_official_metric_fixtures.py
PYTHONDONTWRITEBYTECODE=1 ../.venvs/mhpv2-stage0/bin/python scripts/validate_mhpv2_stage0.py
```

Completed evidence scripts refuse overwriting selected active outputs; these commands describe the executed procedure, not an instruction to rerun/overwrite it. The first audit launch from workspace used `datasets/LV-MHP-v2`; when invoked from study it still resolves root from script location. Incremental revision inspects only GT behind failed RGB images and preserves initial snapshots/source.

Exact tested package freezes are [audit environment](env_specs/mhpv2-stage0.txt) and [FASHN import environment](env_specs/fashn-stage0.txt). New audit packages were pinned; FASHN Torch/CUDA came from the existing verified uv cache without modifying YOLO. Install commands/logs, hardware, official metadata/license snapshots, source SHA values, fixed input IDs and outputs reside in the active run directory. Python bytecode writes were disabled.

Prediction/schema/synthetic metric utilities are tested; no intended-checkpoint smoke or real accuracy/timing result exists. `smoke_fashn.py` is a bounded future helper (1–3 fixed train IDs, FP32, no ranking), currently blocked by dataset and user download decision. It must not be launched until both gates are resolved. No other model adapter is claimed executable.

PPSS was excluded from data reads/tests/validation and remains paused. Validators operate on explicit MHP/new-source artifacts; they must not run existing PPSS audit scripts or glob PPSS results for validation. Full benchmark entrypoints, training/fusion/color workers were not launched.
