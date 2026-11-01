# Body Extraction Human — current status

**V1_END_TO_END_VERIFIED_ON_T4** — local server application, not public hosting or
an independent accuracy/deployment certification.

Current extension: **VIDEO_APPEARANCE_SEARCH_WITH_OBSERVED_TIMESTAMPS**.
Select an exact completed video analysis, filter same-person clothing colors,
inspect paginated matching frame timestamps and open exact person/frame/video
position. No tracking/continuous-interval claim. Three read-only integration
checks and real-browser verification use saved QA video outputs; no new inference.

- Real pipeline: YOLO26x-Seg → controlled Sapiens2 1B person ROI/native29 → owned
  garment masks → selected T4 MLP + separately named observed RGB palette.
- React/TypeScript frontend, authenticated FastAPI, separate durable PostgreSQL
  worker, private persistent file storage and schema migration are implemented.
- Actual-file checks passed: multiple people, no people, artificial occlusion,
  H.264 MP4 with real PTS, color AND search and exact person/frame deep link.
- Actual API/worker/PostgreSQL restart preserved all ten initial person records.
  Missing-file failure/manual retry retained failed attempt and produced one
  current frame. Queued cancel and deletion/byte-range video checks passed.
- Eight CPU/security/lease tests passed. Real Chromium checks passed for Thai
  pages, preview, person selection, search, refresh and video frame/seek.
- Additional final execution-source check passed two new image uploads/four ROIs
  on Tesla T4, reusing the same parser and detector processes across jobs.
- See [verification](docs/VERIFICATION_TH.md) and [aggregate evidence](docs/VERIFICATION.json).

Open `http://127.0.0.1:8038` on the server, or SSH-forward port8038 from a laptop.
Private account/password and owned PID records: `.runtime/app.env` / services.json.
Use `python3 Body_Extraction_Human/scripts/services.py status` from workspace root.
API and worker are detached; no Codex conversation is needed for queued work.

Limitations remain: partial observations/occlusion, visible color under lighting,
Sapiens generic garment categories and Face_Neck, uncalibrated color outputs,
pretrained model usage terms, bounded testing rather than arbitrary-media or
concurrency guarantees. No latency/FPS ranking or CCTV deployment acceptance.
The app's palette vocabulary adapter is distinct from the fitted CCIHP12 head.

Next: user logs in, uploads an authorized new file, verifies its result, and uses
search. No further benchmark/training/download or public network exposure is
queued automatically. Routine application improvement can use this source; keep
scientific experiments and private files untouched.
