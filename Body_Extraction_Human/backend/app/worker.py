"""Durable PostgreSQL queue. One worker owns an advisory lock, one GPU pipeline.

Each committed frame is one database transaction. Failed/lost attempts remain
immutable. A manual retry gets a fresh attempt; queries never mix attempts.
"""

from pathlib import Path
from datetime import datetime, timezone
import json, os, select, shutil, socket, subprocess, threading, time, traceback, uuid
import numpy as np
from PIL import Image
from psycopg.types.json import Jsonb
from . import settings as s, db
from .media import sample_frames


def utc():
    return datetime.now(timezone.utc).isoformat()


def rel(p):
    return str(Path(p).relative_to(s.STORAGE))


class ModelClient:
    def __init__(self, role, root):
        python = {
            "detector": s.ENV_YOLO,
            "parser": s.ENV_SAPIENS if s.PARSER == "sapiens2_1b" else s.ENV_QANET,
            "color": s.ENV_YOLO,
        }[role]
        self.log = (root / (role + ".log")).open("ab", buffering=0)
        env = os.environ.copy()
        env.update(
            BODY_WORKSPACE=str(s.WORKSPACE),
            OMP_NUM_THREADS="2",
            OPENBLAS_NUM_THREADS="2",
            PYTHONUNBUFFERED="1",
        )
        self.p = subprocess.Popen(
            [
                str(python),
                "-u",
                str(s.PROJECT / "scripts/inference_host.py"),
                "--role",
                role,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.log,
            env=env,
            start_new_session=True,
        )
        self.buffer = b""
        try:
            self.identity = self.call(
                dict(
                    op="init",
                    device=s.DEVICE,
                    parser=s.PARSER,
                    color_source=str(s.COLOR_SOURCE),
                    runtime_path=str(root / "runtime"),
                    expected_source_sha256=s.EXECUTION_HASHES[
                        "scripts/inference_host.py"
                    ],
                )
            )
        except BaseException:
            self.close()
            raise

    def call(self, request):
        self.p.stdin.write((json.dumps(request) + "\n").encode())
        self.p.stdin.flush()
        deadline = time.monotonic() + s.MODEL_TIMEOUT
        while time.monotonic() < deadline:
            if b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                if line.startswith(b"@@BODY@@"):
                    reply = json.loads(line[8:])
                    if not reply["ok"]:
                        raise RuntimeError(reply["error_type"] + ": " + reply["error"])
                    return reply["result"]
                self.log.write(line + b"\n")
                continue
            if self.p.poll() is not None:
                raise RuntimeError("MODEL_HOST_EXITED_" + str(self.p.returncode))
            if select.select([self.p.stdout], [], [], 1)[0]:
                chunk = os.read(self.p.stdout.fileno(), 65536)
                if not chunk:
                    raise RuntimeError("MODEL_HOST_PIPE_CLOSED")
                self.buffer += chunk
        raise RuntimeError("MODEL_OPERATION_TIMEOUT")

    def close(self):
        if self.p.poll() is None:
            self.p.terminate()
            try:
                self.p.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.p.kill()
                self.p.wait()
        self.log.close()


def reconcile_lost():
    # Expired lease means external interruption, not evidence of OOM.
    error = Jsonb(
        dict(
            code="WORKER_LOST",
            message="Worker heartbeat expired. Saved committed frames retained; manual retry required.",
            retry_automatic=False,
        )
    )
    with db.connect() as c:
        rows = c.execute(
            "UPDATE jobs SET status='FAILED',error=%s,finished_at=now() WHERE status='RUNNING' AND (heartbeat IS NULL OR heartbeat<now()-interval '90 seconds') RETURNING id,attempt",
            (error,),
        ).fetchall()
        for row in rows:
            c.execute(
                "UPDATE attempts SET status='FAILED',error=%s,finished_at=now() WHERE job_id=%s AND number=%s",
                (error, row["id"], row["attempt"]),
            )


def claim():
    with db.connect() as c:
        row = c.execute(
            "SELECT * FROM jobs WHERE status='QUEUED' AND NOT cancel_requested ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
        ).fetchone()
        if not row:
            return None
        aid = uuid.uuid4().hex
        row = c.execute(
            "UPDATE jobs SET status='RUNNING',attempt=attempt+1,started_at=now(),heartbeat=now(),worker=%s,completed_frames=0,processed_people=0 WHERE id=%s RETURNING *",
            (f"{socket.gethostname()}:{os.getpid()}", row["id"]),
        ).fetchone()
        c.execute(
            "INSERT INTO attempts(id,job_id,number,status) VALUES(%s,%s,%s,'RUNNING')",
            (aid, row["id"], row["attempt"]),
        )
        row["attempt_id"] = aid
        return row


def execute(job, hosts=None):
    jid = job["id"]
    attempt = job["attempt"]
    aid = job["attempt_id"]
    root = s.STORAGE / "jobs" / jid / f"attempt-{attempt:03d}"
    root.mkdir(parents=True, exist_ok=False)
    hosts = hosts if hosts is not None else {}
    stop = threading.Event()
    start = time.monotonic()
    import hashlib

    source_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [
            s.PROJECT / "scripts/inference_host.py",
            s.PROJECT / "scripts/color_contract.py",
            Path(__file__),
        ]
    }
    media = db.one("SELECT * FROM media WHERE id=%s", (job["media_id"],))

    def heartbeat():
        while not stop.wait(10):
            try:
                with db.connect() as c:
                    c.execute(
                        "UPDATE jobs SET heartbeat=now() WHERE id=%s AND status='RUNNING'",
                        (jid,),
                    )
            except Exception:
                pass

    threading.Thread(target=heartbeat, daemon=True).start()

    def event(kind, **kwargs):
        with (root / "events.jsonl").open("a") as f:
            f.write(json.dumps(dict(utc=utc(), event=kind, **kwargs)) + "\n")
            f.flush()
            os.fsync(f.fileno())

    status = "FAILED"
    err = None
    provenance = {
        "application_config": job["config"],
        "input_sha256": media["sha256"],
        "hosts": {},
        "new_file_inference": True,
    }
    try:
        if job["config"] != s.config_snapshot():
            raise RuntimeError(
                "QUEUED_CONFIGURATION_CHANGED: create a new job explicitly"
            )
        if not media:
            raise RuntimeError("SOURCE_MEDIA_MISSING")
        event("START", attempt=attempt)
        for index, t, pts, timebase, rgb in sample_frames(
            s.STORAGE / media["path"], media["kind"], job["sampling_seconds"]
        ):
            current = db.one("SELECT cancel_requested FROM jobs WHERE id=%s", (jid,))
            if current["cancel_requested"]:
                status = "CANCELLED"
                break
            if shutil.disk_usage(s.STORAGE).free < s.MIN_DISK_GIB * 2**30:
                raise RuntimeError("FREE_DISK_GUARD")
            if time.monotonic() - start > 4 * 3600:
                raise RuntimeError("JOB_4H_TIME_GUARD")
            if (
                sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
                > 20 * 2**30
            ):
                raise RuntimeError("ATTEMPT_20GiB_STORAGE_GUARD")
            frame_id = uuid.uuid4().hex
            directory = root / (f"frame-{index:06d}.partial")
            directory.mkdir()
            image = directory / "frame.png"
            Image.fromarray(rgb).save(image)
            if "detector" not in hosts:
                hosts["detector"] = ModelClient("detector", root)
            detection = hosts["detector"].call(
                dict(op="infer", image=str(image), out=str(directory))
            )
            with np.load(detection["path"], allow_pickle=False) as a:
                boxes = a["boxes"].copy()
                scores = a["scores"].copy()
            people = []
            if len(boxes) and "parser" not in hosts:
                hosts["parser"] = ModelClient("parser", root)
            if len(boxes) and "color" not in hosts:
                hosts["color"] = ModelClient("color", root)
            for i, box in enumerate(boxes):
                pdir = directory / f"person-{i + 1:03d}"
                pdir.mkdir()
                details = hosts["parser"].call(
                    dict(
                        op="infer",
                        image=str(image),
                        out=str(pdir),
                        detector=detection["path"],
                        ordinal=i,
                    )
                )
                color = hosts["color"].call(
                    dict(
                        op="infer",
                        image=str(image),
                        out=str(pdir),
                        native=str(pdir / "native.png"),
                    )
                )
                pid = uuid.uuid4().hex
                people.append(
                    dict(
                        id=pid,
                        ordinal=i + 1,
                        bbox=box.tolist(),
                        confidence=float(scores[i]),
                        details=details,
                        color=color,
                        dir=pdir.name,
                    )
                )
            commit = dict(
                frame_id=frame_id,
                index=index,
                timestamp_seconds=t,
                original_pts=pts,
                time_base=timebase,
                input_hw=list(rgb.shape[:2]),
                detector={**detection, "path": "detector.npz"},
                people=people,
                attempt=attempt,
                config=job["config"],
            )
            (directory / "COMMIT.json").write_text(
                json.dumps(commit, ensure_ascii=False, allow_nan=False)
            )
            final = root / f"frame-{index:06d}"
            os.replace(directory, final)
            # DB references appear only after all files are committed. Orphans are
            # retained if the process dies between rename and transaction commit.
            with db.connect() as c:
                c.execute(
                    "INSERT INTO frames(id,job_id,attempt,sample_index,timestamp_seconds,original_pts,time_base,width,height,path) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        frame_id,
                        jid,
                        attempt,
                        index,
                        t,
                        pts,
                        timebase,
                        rgb.shape[1],
                        rgb.shape[0],
                        rel(final / "frame.png"),
                    ),
                )
                for person in people:
                    pd = final / person["dir"]
                    color = person["color"]
                    c.execute(
                        "INSERT INTO persons(id,frame_id,ordinal,bbox,confidence,crop_path,mask_path,parsing_path,native_path,upper_colors,lower_colors,garment_types,upper_result,lower_result,details) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (
                            person["id"],
                            frame_id,
                            person["ordinal"],
                            Jsonb(person["bbox"]),
                            person["confidence"],
                            rel(pd / "crop.png"),
                            rel(pd / "instance.png"),
                            rel(pd / "parsing.png"),
                            rel(pd / "native.png"),
                            color["upper"]["colors"],
                            color["lower"]["colors"],
                            color["garment_types"],
                            Jsonb(color["upper"]),
                            Jsonb(color["lower"]),
                            Jsonb(person["details"]),
                        ),
                    )
                c.execute(
                    "UPDATE jobs SET completed_frames=completed_frames+1,processed_people=processed_people+%s,last_timestamp=%s,heartbeat=now() WHERE id=%s",
                    (len(people), t, jid),
                )
            event(
                "FRAME_COMMITTED",
                sample_index=index,
                people=len(people),
                timestamp_seconds=t,
            )
        else:
            status = "SUCCEEDED"
        if db.one("SELECT cancel_requested FROM jobs WHERE id=%s", (jid,))[
            "cancel_requested"
        ]:
            status = "CANCELLED"
    except BaseException as exc:
        err = dict(
            code=type(exc).__name__, message=str(exc)[:1600], retry_automatic=False
        )
        (root / "ERROR.txt").write_text(traceback.format_exc())
        event("ERROR", code=type(exc).__name__)
    finally:
        for role, host in hosts.items():
            provenance["hosts"][role] = {**host.identity, "process_pid": host.p.pid}
        if status == "FAILED":
            for host in hosts.values():
                host.close()
            hosts.clear()
        stop.set()
        provenance.update(
            duration_seconds=time.monotonic() - start,
            finished_utc=utc(),
            source_hashes=source_hashes,
        )
        (root / "PROVENANCE.json").write_text(json.dumps(provenance, indent=2))
        with db.connect() as c:
            c.execute(
                "UPDATE jobs SET status=%s,error=%s,finished_at=now(),heartbeat=now(),total_frames=CASE WHEN %s='SUCCEEDED' THEN completed_frames ELSE total_frames END WHERE id=%s",
                (status, Jsonb(err) if err else None, status, jid),
            )
            c.execute(
                "UPDATE attempts SET status=%s,error=%s,finished_at=now(),provenance=%s WHERE id=%s",
                (status, Jsonb(err) if err else None, Jsonb(provenance), aid),
            )
        event("FINISH", status=status)


def main():
    db.migrate()
    lock = db.connect()
    lock.autocommit = True
    if not lock.execute("SELECT pg_try_advisory_lock(723081938) locked").fetchone()[
        "locked"
    ]:
        raise RuntimeError("ANOTHER_BODY_EXTRACTION_WORKER_IS_RUNNING")
    print(
        json.dumps(dict(status="WORKER_READY", pid=os.getpid(), parser=s.PARSER)),
        flush=True,
    )
    hosts = {}
    last_work = time.monotonic()
    try:
        while True:
            reconcile_lost()
            job = claim()
            if job:
                execute(job, hosts)
                last_work = time.monotonic()
            else:
                if hosts and time.monotonic() - last_work > 300:
                    for host in hosts.values():
                        host.close()
                    hosts.clear()
                time.sleep(2)
    finally:
        for host in hosts.values():
            host.close()


if __name__ == "__main__":
    main()
