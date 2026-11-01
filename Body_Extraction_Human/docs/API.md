# Authenticated API quick reference

FastAPI OpenAPI schema: `/openapi.json`; interactive documentation: `/docs`.
Log in with `POST /api/login` JSON username/password; keep the HTTP-only cookie.
All mutations except login require `X-Requested-With: BodyExtraction` and a
same-origin request. Shared one-operator scope; no unauthenticated result URLs.

| Method/path | Operation |
|---|---|
| GET `/api/health` | Minimal public DB liveness |
| POST `/api/login` | Establish signed 12-hour session |
| GET `/api/me` / POST `/api/logout` | Session management |
| GET `/api/ready` | Asset availability, configured parser, limits (not a model execution claim) |
| POST `/api/media` | Multipart file, source, optional timezone-aware event_start |
| POST `/api/jobs` | JSON media_id, sampling_seconds; durable enqueue |
| GET `/api/jobs?page=1` | Persistent job list, 20/page |
| GET `/api/jobs/{id}` | Status, real frame/person counts, current frames, attempts, partial flag |
| POST `/api/jobs/{id}/cancel` | Request stop between frames or cancel queued job |
| POST `/api/jobs/{id}/retry` | Manual fresh attempt for FAILED/CANCELLED |
| GET `/api/frames/{id}` | Original-grid frame and persons, crop/mask/color references |
| GET `/api/search` | Completed current-attempt person search with AND filters |
| GET `/api/video-jobs` | Paginated searchable completed video analyses for exact clip/job selection |
| GET `/api/files/{asset}` | Authenticated original/crop/mask/video; range requests supported |
| DELETE `/api/media/{id}` | Delete source + dependent jobs/results/files; rejects RUNNING |

Search query fields: upper/lower observed color name, garment (supported native
type only), kind=image/video, q=filename or source, uploaded_from/uploaded_to,
event_from/event_to (timezone-aware ISO timestamps, upper bound exclusive), page,
page_size<=60. Event filters naturally exclude unknown event starts. Color filters
match dominant/secondary labels with >=15% observed palette support, not MLP
softmax thresholds or identity. Person rows in the same frame remain independent.

Record identities: media UUID → job UUID → numbered immutable attempt → frame UUID
with sample_index/PTS/timebase/timestamp_seconds → person UUID and ordinal within
that frame. Ordinal is not a persistent track ID. Confidence is the YOLO detector
score only. Unknown colors have empty arrays/null learned label and a reason.

UI deep link: `/#job=JOB_ID&frame=FRAME_ID&person=PERSON_ID` selects the exact
matching observation. Video controls seek to actual frame timestamp, not upload
time. Saved result references are rooted under storage, never user-provided paths.

Video search extension: `job_id` selects one exact completed analysis, avoiding
filename ambiguity and mixing repeated analyses. `time_from_seconds` and
`time_to_seconds` are inclusive relative-clip bounds and restrict results to video.
A reversed interval is422. `include_moments=true` returns `moments` and
`total_moments`; their independent pagination is `moment_page` and
`moment_page_size` (default12,max60). No timeline requested -> these fields are
null, not zero. The same person-level filters/domain/current-attempt conditions
produce both cards and moments. Each moment has actual timestamp, frame/job IDs,
sampling interval and matching person's IDs/ordinals. Several matches in one
frame count as one moment with multiple observations, not identity tracks.
Moment rows never turn gaps into continuous presence intervals.

`GET /api/video-jobs?q=...&page=1&page_size=50` searches completed video jobs by
filename/source, with100/page maximum. All endpoints remain authenticated.
Search entry deep link: `/#search&video_job=JOB_ID`.
