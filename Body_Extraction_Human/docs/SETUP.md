# Setup and external artifact specification

All paths below are relative to `BODY_WORKSPACE`, default the parent of this app.
Set `BODY_WORKSPACE`, `BODY_STORAGE` and `BODY_COLOR_SOURCE` to relocate bindings;
do not move installed environments or rewrite historical benchmark records.

| Resource | Existing location | Purpose |
|---|---|---|
| API Python | `.venvs/body-extraction-api/bin/python` | FastAPI/DB/PyAV, no torch |
| YOLO/color Python | `.venv/bin/python` | Existing Ultralytics, torch, sklearn, OpenCV |
| Sapiens Python | `.venvs/sapiens2-pilot/bin/python` | Existing compatible Sapiens2 source/runtime |
| Alternative QANet Python | `.venvs/parser-legacy-cu113/bin/python` | Existing accepted legacy adapter |
| YOLO weights | `models/yolo26x-seg.pt` | External, loader hash checked |
| Sapiens weights | `models/human_parsing/sapiens2/1b/sapiens2_1b_seg.safetensors` | External, loader hash checked |
| Sapiens source/config | `third_party/human_parsing/sapiens2/` | Source revision and terms in implementation |
| Existing crop adapters | `CCTV_Human_Parsing_Benchmark/scripts/` | Read-only geometry/QANet integration |
| Model records | This app's `configs/MODEL_BINDINGS.json` | Sanitized exact selected identities extracted from accepted records; no image memberships or historical execution required |
| Color source | sibling `Garment-Color-Extractor/src/garment_color` | MIT source, explicit external dependency |
| Color weights | sibling `Garment-Color-Extractor/outputs/t4-pilot-20261101/learned_color.pt` | Authorized local fitted artifact, not bundled |

No private historical config/outputs or dataset membership is needed by the app.
The selected model-only registry is included in Git; external source/weights still
need local preparation. Missing dependencies report unavailable, never fake output.

API environment is newly isolated. Existing working YOLO/Sapiens environments
were reused without pip modifications. `requirements.lock.txt` captures the
actual new API installation. Existing model environment versions are recorded by
the inference hosts in attempt provenance. React dependencies are in package-lock.

Default database uses a new app-only PostgreSQL15 container/volume on loopback
port55438. No connection to or mutation of other running PostgreSQL containers.
`scripts/bootstrap.py` generates random local secrets once and reuses them.

Tesla T4 is the available target. The parser supports an explicit CPU device in
its adapter; full Sapiens CPU end-to-end execution is not claimed tested. QANet's
existing adapter is CUDA-only. Change `BODY_DEVICE` explicitly then restart API
and worker and create a new job; no silent fallback or guaranteed speed.

GPU sharing does not eliminate free-memory guards. The app admits Sapiens loading
only with >=7GiB free, and detector with >=1GiB, as conservative engineering guards,
not proof all inputs fit. Any CUDA/OOM error fails the current attempt and retains
committed frames; manual retries do not change precision/resolution.

For production network access, terminate TLS with a reverse proxy, set secure
cookies, replace local credentials, restrict upload/video budgets for the intended
users and back up both PostgreSQL/storage. No public hosting was created here.
