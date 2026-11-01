# Body Extraction Human application

Start README → STATUS → docs/IMPLEMENTATION.md → docs/VERIFICATION_TH.md.
This is the application source, separate from frozen scientific experiments.

- User authorized building and bounded actual-file testing of the web application
  with YOLO26x-Seg, selected Sapiens2 1B and selected T4 MLP. A completed test report
  is historical evidence, not permission to relaunch old benchmarks or training.
- Inspect owned services/queue/GPU before any process or model launch. API and
  worker are detached; do not duplicate or kill other services/GPU processes.
- Use the existing model environments without modifying them; API dependencies
  belong in `.venvs/body-extraction-api`. Shared assets stay in models/third_party.
- Keep uploads, private RGB/crops/masks/video, credentials, per-person records,
  logs and browser screenshots under ignored storage/ or .runtime/ only.
- No placeholder model predictions, no half-box garment splitting, no GT-derived
  predictions or identity recognition. Native labels, detector confidence,
  learned color scores and observed-palette fractions have separate meanings.
- Unknown remains null/empty with a reason, never black. Do not hide the Sapiens
  category ambiguity or license terms. Integration does not grant usage rights.
- All new inference/scoring writes use fresh application attempts. Never alter
  frozen YOLO/parsing/color benchmark results or original datasets.
- Source/public checkouts are separate; sync only explicit allowed source/docs/
  aggregate files, review diff/secrets/size and commit normally without force.
- Final local services and credentials are in private .runtime/, not Git. A public
  clone needs external source/checkpoints/environments, not private CCTV assets.
