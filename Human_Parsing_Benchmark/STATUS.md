# Human Parsing Benchmark — current status

Updated: 2026-10-28T09:33:52.036825+00:00 UTC

**FINISHED_WITH_INCOMPLETE_SYSTEMS** — official native CIHP validation 5,000 images per system, 3/6 systems complete. Run `cihp-native-six-20261028T034103254470Z`. [Result report](reports/cihp-native-six-20261028T034103254470Z/REPORT_TH.md) / [completion](runs/cihp-native-six-20261028T034103254470Z/COMPLETION.json) / [PLAN](PLAN.md).

STRICT_COMPLETE: main scores remain null for incomplete systems; their failure/pending rows are retained. Launch commit `5e8f36ae2a249295c6a1b424b066b010449da048` identifies execution code, not the later reporting/publication commit. Original controller and model attempts are preserved; no automatic failed-image retries or changed inference settings.

Fixed 16-image original-grid comparisons are external under the run artifact root, `QUALITATIVE/index.html`. See completion for hashes and location. Cached YOLO means end-to-end FPS was not measured; parser timing/VRAM scopes remain explicit.

Next: review terminal results/failures and continuation evidence. Matrix/Sapiens/color execution is not started by this continuation. No Ninja, training or CCTV processing was started. Old YOLO/CPI results and source GT remain unchanged.
