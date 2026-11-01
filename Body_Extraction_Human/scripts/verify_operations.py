"""Bounded actual-service restart/retry/delete checks, after inference QA finishes.

Only this app's processes/container/files are touched. No original dataset,
model environment, checkpoint, benchmark result or other service is changed.
"""

from pathlib import Path
from datetime import datetime, timezone
import json, os, signal, subprocess, sys, time
import httpx

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / "backend"))
from app import settings as s, db


def main():
    if db.one("SELECT count(*) n FROM jobs WHERE status IN ('RUNNING','QUEUED')")["n"]:
        raise RuntimeError(
            "Wait for current app verification queue to finish; no interruption allowed"
        )
    out = P / ".runtime/verification"
    result = dict(started_utc=datetime.now(timezone.utc).isoformat())
    before = db.all_rows("SELECT id,frame_id FROM persons ORDER BY id")
    subprocess.run([sys.executable, str(P / "scripts/services.py"), "stop"], check=True)
    time.sleep(3)
    subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(P / ".runtime/app.env"),
            "-p",
            "body-extraction-human",
            "-f",
            str(P / "compose.yaml"),
            "restart",
            "postgres",
        ],
        check=True,
    )
    for _ in range(30):
        try:
            db.one("SELECT 1")
            break
        except Exception:
            time.sleep(1)
    subprocess.run(
        [sys.executable, str(P / "scripts/services.py"), "start"], check=True
    )
    c = httpx.Client(
        base_url="http://127.0.0.1:8038",
        timeout=60,
        headers={"X-Requested-With": "BodyExtraction"},
    )
    for _ in range(20):
        try:
            if c.get("/api/health").status_code == 200:
                break
        except httpx.TransportError:
            pass
        time.sleep(1)
    c.post(
        "/api/login", json=dict(username=s.USERNAME, password=s.PASSWORD)
    ).raise_for_status()
    assert db.all_rows("SELECT id,frame_id FROM persons ORDER BY id") == before
    result["API_worker_PostgreSQL_restart_preserves_person_records"] = len(before)
    worker = json.loads((P / ".runtime/services.json").read_text())["worker"]
    assert (
        "app.worker"
        in (Path("/proc") / str(worker["pid"]) / "cmdline").read_bytes().decode()
    )
    os.kill(worker["pid"], signal.SIGTERM)
    time.sleep(2)

    def upload():
        with (out / "empty.png").open("rb") as f:
            r = c.post("/api/media", files={"file": ("operations-fixture.png", f)})
        r.raise_for_status()
        return r.json()

    def enqueue(mid):
        r = c.post("/api/jobs", json=dict(media_id=mid, sampling_seconds=1))
        r.raise_for_status()
        return r.json()

    m = upload()
    j = enqueue(m["id"])
    assert c.post("/api/jobs/" + j["id"] + "/cancel").json()["status"] == "CANCELLED"
    assert c.get("/api/jobs/" + j["id"]).json()["attempt"] == 0
    assert c.delete("/api/media/" + m["id"]).status_code == 200
    result["queued_cancel_without_model_call"] = True
    m = upload()
    path = s.STORAGE / m["path"]
    held = path.with_suffix(".held")
    path.rename(held)
    j = enqueue(m["id"])
    subprocess.run(
        [sys.executable, str(P / "scripts/services.py"), "start"], check=True
    )

    def wait_terminal(jid, seconds=180):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            row = c.get("/api/jobs/" + jid).json()
            if row["status"] not in ("QUEUED", "RUNNING"):
                return row
            time.sleep(1)
        raise RuntimeError("Verification job did not finish within bound")

    failed = wait_terminal(j["id"])
    assert failed["status"] == "FAILED" and failed["completed_frames"] == 0
    held.rename(path)
    c.post("/api/jobs/" + j["id"] + "/retry").raise_for_status()
    retried = wait_terminal(j["id"])
    assert (
        retried["status"] == "SUCCEEDED"
        and retried["completed_frames"] == 1
        and retried["processed_people"] == 0
    )
    assert [a["status"] for a in retried["attempts"]] == [
        "FAILED",
        "SUCCEEDED",
    ] and retried["attempt"] == 2
    assert len(retried["frames"]) == 1
    result["real_missing_file_failure_and_manual_retry"] = dict(
        attempts=2, current_frames=1, old_failure_retained=True
    )
    frame_path = retried["frames"][0]["path"]
    assert c.get("/api/files/" + frame_path).status_code == 200
    assert c.delete("/api/media/" + m["id"]).status_code == 200
    assert (
        c.get("/api/jobs/" + j["id"]).status_code == 404
        and c.get("/api/files/" + frame_path).status_code == 404
    )
    result["delete_database_and_assets"] = True
    run = json.loads((out / "RESULTS.json").read_text())
    clip = c.get("/api/jobs/" + run["cases"]["clip.mp4"]["job_id"]).json()
    r = c.get("/api/files/" + clip["media_path"], headers={"Range": "bytes=0-255"})
    assert r.status_code == 206 and len(r.content) == 256
    result["authenticated_video_byte_range_206"] = True
    result["finished_utc"] = datetime.now(timezone.utc).isoformat()
    (out / "OPERATIONS.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
