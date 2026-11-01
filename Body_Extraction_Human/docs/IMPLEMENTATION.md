# Body Extraction Human — implementation and boundaries

This application is independent of frozen benchmark execution and outputs. Its
versioned source lives at the workspace root in `Body_Extraction_Human`.

## Actual architecture

React + TypeScript + Vite builds a same-origin frontend served by FastAPI.
PostgreSQL 15 stores media, queued jobs, immutable attempts, timestamped frames,
persons and color results. The separate Python worker claims queued rows with
`FOR UPDATE SKIP LOCKED`, guarded by one PostgreSQL advisory lock for this app.
This follows PostgreSQL's documented queue-consumer use of [SKIP LOCKED](https://www.postgresql.org/docs/current/sql-select.html).

Each model runs in its existing isolated environment over private JSON-line IPC.
No API request loads a model. One worker handles one frame at a time, batching no
person ROIs, and reads video incrementally with PyAV/FFmpeg. Models can remain
resident across jobs; the worker releases them after five idle minutes. Processes
are started detached; starting services again does not duplicate owned services.

Model environments and shared assets are resolved relative to `BODY_WORKSPACE`.
No weights, environments, CCTV data or benchmark outputs are moved or modified.
Raw application files belong to `BODY_STORAGE` (default `storage/`, ignored).

## Pipeline and model provenance

1. Real YOLO26x-Seg weights `models/yolo26x-seg.pt`, SHA256
   `92b3de0065766a17180d6219858717dc9d03cdce8a3ca9576c97fd75aabb64f3`.
   Person-only, FP32, imgsz640/conf0.25/IoU0.7/maxdet200/retina masks.
2. Preferred parser: Sapiens2 segmentation 1B, actual recorded module has
   1,470,819,805 parameters. Weights SHA256
   `4b73c44963b377e93fcb4c4053f72a189836a22d05e12c30383046b9cd3c5bd4`.
   Reuse the accepted original-RGB crop adapter: predicted box +10% context on
   each side, expanded to contain the detector mask, clamped to the image.
   Aspect-preserving 1024H×768W mean-color letterbox; official BGR-to-RGB
   normalization exactly once; remove padding and interpolate logits back before
   argmax. Full original-grid native29 masks retained. Clip with this detected
   person's instance mask. FP32/batch1/eval/inference mode; no AMP, TF32 or TTA.
3. Optional explicit `BODY_PARSER=qanet`: the previously accepted CIHP HRNet-W48
   512×384 adapter, original native20 labels. Changing parser requires restarting
   API/worker, then creating a new job. No automatic fallback or mixed outputs.
4. Selected color model: `T4_MLP_62_64_32_12_v1`, 6,508 parameters; exact artifact
   SHA256 `4145b416f9020422e389210af6eab6adc6d92d6c37af6033f60ffc712969bfde`.
   Original RGB pixels inside the owned garment masks; existing erosion and 58D
   LAB/HSV features + four category inputs. No overlay pixels used. Model runs on
   CPU in the existing compatible YOLO environment. See sibling
   `Garment-Color-Extractor/registry/SELECTED_METHOD.json`.

The checkpoint/config bindings are read from existing accepted local model
records, not downloaded. Loaders hash selected weights/configs before use.
Each job records configuration; each attempt records input hash, host/model
identities, software/source hashes and outcome. These are application attempts,
not new benchmark or accuracy measurements.

## Honest garment and color contract

Sapiens native23 Upper_Clothing / native13 Lower_Clothing do not establish Coat,
Pants or Skirt. The app labels them **เสื้อผ้าส่วนบน / เสื้อผ้าส่วนล่าง**. It never
splits Apparel/native1 into upper/lower. Native29 stays available in the mask.

The learned color model expects CIHP categories5/7/9/12. For Sapiens generic
Upper, evaluate the same pixels under category5 and7; for Lower,9 and12. Return
the learned color only if these agree; otherwise learned color is null with
`category_or_layer_ambiguous`. Record each hypothesis and its uncalibrated
softmax. This declared application adapter has not inherited the oracle benchmark
accuracy claim. QANet uses its actual categories5/7/9/12; coats/skirt are not
inferred from box geometry.

Separately, an **observed palette** groups the existing deterministic CIELAB
clusters using a documented HSV engineering vocabulary of twelve familiar colors.
It supplies swatches and dominant/secondary search labels. Aggregate identical
names before selecting up to two colors with >=15% pixel support. This observed
palette is not claimed to be the trained model's 12-class label: its classes are
black/white/gray/red/orange/yellow/green/sky_blue/blue/purple/pink/brown, while the
trained model uses Dark/Medium/Light/.../Multicolor. The UI shows both separately.
Pixel fractions and softmax are never presented as calibrated accuracy confidence.

Fewer than40 cleaned garment pixels -> unknown/null, empty color list and reason,
never black as a missing value. Occlusion can be reported through absent/small
regions; there is no validated automatic occlusion estimator. Near-grayscale
appearance cannot establish original visible-light hue. Exposure, lighting, mask
contamination, shade and patterns remain limitations; the app does not recover
intrinsic fabric color.

## Video and persistence

Use actual decoded PTS×time_base relative to the first decodable frame. Uniform
sampling selects the first actual frame at/after each interval, without storing
the entire clip in memory. Keep original PTS/timebase and actual timestamps.
Duplicate records across frames are independent observations, not identity or
tracks. Event time is `user-supplied timezone-aware clip start + frame timestamp`;
missing event start stays null, never upload time. Decoder errors and missing or
nonmonotonic timestamps fail explicitly; earlier committed frames are partial.
MP4 codecs are those accepted by installed FFmpeg. H.264 is tested; browser codec
support may differ from server decoding. No silent video transcoding.

Each frame is written into a fresh partial directory, then committed by rename,
then inserted with all persons in one DB transaction. Unique keys prevent duplicate
frame/person entries. A crash between rename and DB commit can leave an unindexed
orphan, which remains private and is not treated as a successful frame. Manual
retry creates a fresh attempt; old attempts are retained, not combined or selected
by score. Current results and search use only the current attempt. Search excludes
incomplete/cancelled attempts and ANDs all conditions on the same person row.

Workers heartbeat every10s. On restart or lease expiration (>90s), interrupted
RUNNING attempts become FAILED/WORKER_LOST; no automatic model/OOM retry. A model
host exits if its owning worker dies. User cancellation takes effect between
frames, after atomic writes; the current inference may finish first. API restart
does not stop the worker. DB/storage survive service and container restarts.

## Security and operational defaults

One operator account, environment-configured password; signed HTTP-only,
SameSite=Strict, 12-hour cookie. Mutations require a custom header and reject a
foreign Origin. All upload/result/search/file endpoints require authentication.
Files use generated storage paths, traversal is rejected and downloads stay
authenticated. Upload streaming limit500MiB, max40M pixels, video<=1h,
<=3,600 sampled frames, free disk>=20GiB, per-attempt20GiB/4h guards. No arbitrary
public upload URL. Logs omit image content and user original filenames.

Default binding is127.0.0.1:8038. Use SSH forwarding locally. Network deployments
need a TLS reverse proxy and `BODY_COOKIE_SECURE=true`; do not expose PostgreSQL.
No external identity/face recognition, tracking, ReID or cross-camera linkage.

## Sources and usage terms

- [Sapiens2 code/model source](https://github.com/facebookresearch/sapiens2),
  local recorded revision `7e5bae88456ac418ff0e58e74106c9fe192055d4`.
  [Sapiens2 License](https://github.com/facebookresearch/sapiens2/blob/main/LICENSE.md)
  expressly prohibits surveillance, including related research/development.
  User requested integration after disclosure; this request does not grant
  additional model rights. This implementation is not evidence of permission for
  surveillance deployment. No model/source redistribution is performed here.
- [QANet](https://github.com/soeaver/QANet): inspected local source MIT; weight/data
  terms remain applicable to the intended use. Alternative is an explicit choice,
  not a silent substitution for the selected parser.
- [Ultralytics](https://docs.ultralytics.com/): installed YOLO implementation and
  checkpoint remain external; AGPL-3.0/enterprise terms apply as appropriate.
- Sibling Garment-Color-Extractor source MIT, selected fitted artifact provided
  locally, not republished. Color study evidence does not establish deployment
  color accuracy on arbitrary uploads.

This app adds no new first-party license grant on the user's behalf.
