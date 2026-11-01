"""Read-only integration on actual saved QA video outputs. No new inference."""

from pathlib import Path
import json, sys
import pytest
from fastapi.testclient import TestClient

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / "backend"))
from app import settings as s, db
from app.api import app


@pytest.fixture
def video():
    evidence = P / ".runtime/verification/RESULTS.json"
    if not evidence.exists():
        pytest.skip(
            "Requires existing actual QA clip artifacts; no fabricated person results"
        )
    jid = json.loads(evidence.read_text())["cases"]["clip.mp4"]["job_id"]
    row = db.one("SELECT * FROM jobs WHERE id=%s", (jid,))
    if not row or row["status"] != "SUCCEEDED":
        pytest.skip("Actual saved QA clip missing or incomplete")
    with TestClient(app) as client:
        client.headers["X-Requested-With"] = "BodyExtraction"
        assert (
            client.post(
                "/api/login", json=dict(username=s.USERNAME, password=s.PASSWORD)
            ).status_code
            == 200
        )
        yield client, jid


def test_selected_video_and_actual_moment_pagination(video):
    client, jid = video
    expected = db.all_rows(
        "SELECT f.id,f.timestamp_seconds,count(p.id) n FROM frames f JOIN persons p ON p.frame_id=f.id JOIN jobs j ON f.job_id=j.id WHERE j.id=%s AND f.attempt=j.attempt GROUP BY f.id ORDER BY f.timestamp_seconds",
        (jid,),
    )
    r = client.get(
        "/api/search",
        params={"job_id": jid, "include_moments": "true", "moment_page_size": 1},
    ).json()
    assert r["total"] == sum(f["n"] for f in expected) and r["total_moments"] == len(
        expected
    )
    assert all(p["job_id"] == jid for p in r["items"])
    assert r["moments"][0]["timestamp_seconds"] == expected[0]["timestamp_seconds"]
    assert r["moments"][0]["matching_observations"] == expected[0]["n"]
    second = client.get(
        "/api/search",
        params={
            "job_id": jid,
            "include_moments": "true",
            "moment_page_size": 1,
            "moment_page": 2,
        },
    ).json()
    assert second["moments"][0]["frame_id"] == expected[1]["id"]
    assert r["moments"][0]["frame_id"] != second["moments"][0]["frame_id"]


def test_person_AND_filters_agree_with_timeline_and_time_window(video):
    client, jid = video
    row = db.one(
        "SELECT p.*,f.timestamp_seconds,f.id fid FROM persons p JOIN frames f ON f.id=p.frame_id WHERE f.job_id=%s AND cardinality(p.upper_colors)>0 AND cardinality(p.lower_colors)>0 ORDER BY f.timestamp_seconds,p.ordinal LIMIT 1",
        (jid,),
    )
    assert row, "Saved real QA video must have color-searchable observations"
    params = dict(
        job_id=jid,
        upper=row["upper_colors"][0],
        lower=row["lower_colors"][0],
        include_moments="true",
        time_from_seconds=row["timestamp_seconds"],
        time_to_seconds=row["timestamp_seconds"],
    )
    r = client.get("/api/search", params=params).json()
    assert any(p["id"] == row["id"] for p in r["items"])
    assert len(r["moments"]) == 1 and r["moments"][0]["frame_id"] == row["fid"]
    for person in r["items"]:
        assert (
            params["upper"] in person["upper_colors"]
            and params["lower"] in person["lower_colors"]
        )
        assert person["timestamp_seconds"] == row["timestamp_seconds"]
    assert {p["id"] for p in r["moments"][0]["persons"]} == {
        p["id"] for p in r["items"]
    }
    assert (
        client.get(
            "/api/search", params={"time_from_seconds": 2, "time_to_seconds": 1}
        ).status_code
        == 422
    )


def test_video_picker_and_endpoint_auth(video):
    client, jid = video
    rows = client.get("/api/video-jobs", params={"q": "clip.mp4"}).json()
    assert any(r["job_id"] == jid for r in rows["items"])
    with TestClient(app) as anonymous:
        assert anonymous.get("/api/video-jobs").status_code == 401
        assert (
            anonymous.get("/api/search", params={"include_moments": "true"}).status_code
            == 401
        )
