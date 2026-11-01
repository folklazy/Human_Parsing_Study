CREATE TABLE IF NOT EXISTS schema_versions(version integer PRIMARY KEY, applied_at timestamptz DEFAULT now());
CREATE TABLE IF NOT EXISTS media(
 id text PRIMARY KEY, filename text NOT NULL, source text NOT NULL DEFAULT '', kind text NOT NULL,
 path text NOT NULL UNIQUE, bytes bigint NOT NULL, sha256 text NOT NULL,
 metadata jsonb NOT NULL, event_start timestamptz, uploaded_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS jobs(
 id text PRIMARY KEY, media_id text NOT NULL REFERENCES media(id) ON DELETE CASCADE,
 status text NOT NULL DEFAULT 'QUEUED', config jsonb NOT NULL, sampling_seconds double precision NOT NULL,
 attempt integer NOT NULL DEFAULT 0, cancel_requested boolean NOT NULL DEFAULT false,
 completed_frames integer NOT NULL DEFAULT 0, total_frames integer, processed_people integer NOT NULL DEFAULT 0,
 last_timestamp double precision, error jsonb, worker text, heartbeat timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(), started_at timestamptz, finished_at timestamptz
);
CREATE TABLE IF NOT EXISTS attempts(
 id text PRIMARY KEY, job_id text NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
 number integer NOT NULL, status text NOT NULL, started_at timestamptz NOT NULL DEFAULT now(),
 finished_at timestamptz, error jsonb, provenance jsonb, UNIQUE(job_id,number)
);
CREATE TABLE IF NOT EXISTS frames(
 id text PRIMARY KEY, job_id text NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
 attempt integer NOT NULL, sample_index integer NOT NULL, timestamp_seconds double precision NOT NULL,
 original_pts bigint, time_base text, width integer NOT NULL, height integer NOT NULL, path text NOT NULL,
 UNIQUE(job_id,attempt,sample_index)
);
CREATE TABLE IF NOT EXISTS persons(
 id text PRIMARY KEY, frame_id text NOT NULL REFERENCES frames(id) ON DELETE CASCADE,
 ordinal integer NOT NULL, bbox jsonb NOT NULL, confidence double precision NOT NULL,
 crop_path text NOT NULL, mask_path text NOT NULL, parsing_path text NOT NULL, native_path text NOT NULL,
 upper_colors text[] NOT NULL, lower_colors text[] NOT NULL, garment_types text[] NOT NULL,
 upper_result jsonb NOT NULL, lower_result jsonb NOT NULL, details jsonb NOT NULL,
 UNIQUE(frame_id,ordinal)
);
CREATE INDEX IF NOT EXISTS jobs_queue_idx ON jobs(status,created_at);
CREATE INDEX IF NOT EXISTS frames_job_idx ON frames(job_id,attempt,sample_index);
CREATE INDEX IF NOT EXISTS upper_colors_idx ON persons USING gin(upper_colors);
CREATE INDEX IF NOT EXISTS lower_colors_idx ON persons USING gin(lower_colors);
CREATE INDEX IF NOT EXISTS garment_types_idx ON persons USING gin(garment_types);
INSERT INTO schema_versions(version) VALUES(1) ON CONFLICT DO NOTHING;
