"""Two real new uploads on final execution source: validate resident model reuse."""

from pathlib import Path
from datetime import datetime, timezone
import json, sys, time
import httpx

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / "backend"))
from app import settings as s


def main():
    out = P / ".runtime/verification"
    c = httpx.Client(
        base_url="http://127.0.0.1:8038",
        timeout=180,
        headers={"X-Requested-With": "BodyExtraction"},
    )
    c.post(
        "/api/login", json=dict(username=s.USERNAME, password=s.PASSWORD)
    ).raise_for_status()
    ids = []
    for i in range(2):
        with (out / "multi.png").open("rb") as f:
            r = c.post(
                "/api/media",
                files={"file": (f"final-source-{i + 1}.png", f)},
                data={"source": "Final source cache verification"},
            )
        r.raise_for_status()
        media = r.json()
        r = c.post("/api/jobs", json=dict(media_id=media["id"], sampling_seconds=1))
        r.raise_for_status()
        ids.append(r.json()["id"])
    (out / "FINAL_RUNNING.json").write_text(json.dumps(dict(jobs=ids), indent=2))
    deadline = time.monotonic() + 1800
    rows = []
    while time.monotonic() < deadline:
        rows = [c.get("/api/jobs/" + jid).json() for jid in ids]
        if all(row["status"] not in ("QUEUED", "RUNNING") for row in rows):
            break
        time.sleep(5)
    assert all(
        r["status"] == "SUCCEEDED"
        and r["completed_frames"] == 1
        and r["processed_people"] >= 2
        for r in rows
    ), [(r["status"], r["error"]) for r in rows]
    hosts = [r["attempts"][-1]["provenance"]["hosts"] for r in rows]
    assert hosts[0]["parser"]["process_pid"] == hosts[1]["parser"]["process_pid"]
    assert hosts[0]["detector"]["process_pid"] == hosts[1]["detector"]["process_pid"]
    assert all(
        h["parser"]["GPU"] == "Tesla T4" and h["parser"]["model"] == "Sapiens2_1b"
        for h in hosts
    )
    assert all(
        h["parser"]["host_source_sha256"]
        == s.EXECUTION_HASHES["scripts/inference_host.py"]
        for h in hosts
    )
    result = dict(
        status="PASS",
        finished_utc=datetime.now(timezone.utc).isoformat(),
        jobs=ids,
        actual_new_frames=2,
        actual_person_ROI_calls=sum(r["processed_people"] for r in rows),
        parser_process_reused=True,
        detector_process_reused=True,
        GPU=hosts[0]["parser"]["GPU"],
        source_hashes=s.EXECUTION_HASHES,
        primary_model_identity=hosts[0]["parser"],
    )
    (out / "FINAL_SOURCE.json").write_text(json.dumps(result, indent=2))
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("jobs", "source_hashes", "primary_model_identity")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
