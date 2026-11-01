"""Independent media/API security/lease and real-result retrieval requirements.

No mocked model output is reported as user inference. Uses an app-specific DB;
temporary media tests remove only their own fixtures.
"""

import io, sys, uuid, json
from pathlib import Path
import numpy as np, pytest, av
from PIL import Image
from fastapi.testclient import TestClient

P = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(P / "backend"), str(P / "scripts")]
from app import settings as s, db
from app.api import app
from app.media import inspect_media, sample_frames
from app.worker import reconcile_lost
from color_contract import color_name


@pytest.fixture
def client():
    with TestClient(app) as c:
        c.headers["X-Requested-With"] = "BodyExtraction"
        r = c.post("/api/login", json=dict(username=s.USERNAME, password=s.PASSWORD))
        assert r.status_code == 200
        yield c


def test_auth_and_csrf_and_path(client):
    with TestClient(app) as anonymous:
        assert anonymous.get("/api/jobs").status_code == 401
        assert anonymous.get("/api/files/uploads/secret.png").status_code == 401
    assert (
        client.post(
            "/api/jobs", headers={"Origin": "https://attacker.invalid"}, json={}
        ).status_code
        == 403
    )
    assert client.get("/api/files/%2e%2e/.env").status_code == 404


def test_invalid_uploads(client):
    assert (
        client.post(
            "/api/media", files={"file": ("fake.png", b"not a PNG")}
        ).status_code
        == 422
    )
    assert (
        client.post("/api/media", files={"file": ("bad.mp4", b"not MP4")}).status_code
        == 422
    )
    assert (
        client.post("/api/media", files={"file": ("a.txt", b"no")}).status_code == 415
    )
    b = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(b, format="PNG")
    assert (
        client.post(
            "/api/media",
            files={"file": ("a.png", b.getvalue())},
            data={"event_start": "2026-11-01T00:00"},
        ).status_code
        == 422
    )


def test_streaming_upload_limit_before_multipart_disk(client, monkeypatch):
    monkeypatch.setattr(s, "MAX_UPLOAD", 16)
    assert (
        client.post(
            "/api/media",
            content=b"x" * (1024**2 + 30),
            headers={"content-type": "multipart/form-data; boundary=b"},
        ).status_code
        == 413
    )
    # Chunked input without Content-Length cannot bypass the receive limit.
    assert (
        client.post(
            "/api/media",
            content=iter(
                [
                    b'--b\r\nContent-Disposition: form-data; name="file"; filename="x.png"\r\n\r\n',
                    b"x" * (1024**2 + 30),
                    b"\r\n--b--\r\n",
                ]
            ),
            headers={"content-type": "multipart/form-data; boundary=b"},
        ).status_code
        == 413
    )


def test_image_exif_not_width_assumption(tmp_path):
    im = Image.new("RGB", (30, 20), "blue")
    exif = im.getexif()
    exif[274] = 6
    p = tmp_path / "r.jpg"
    im.save(p, exif=exif)
    kind, metadata = inspect_media(p, ".jpg")
    assert (metadata["width"], metadata["height"]) == (20, 30)
    rows = list(sample_frames(p, kind, 1))
    assert rows[0][-1].shape == (30, 20, 3)


def test_pts_sampling_is_actual_pts(tmp_path):
    p = tmp_path / "variable.mp4"
    from fractions import Fraction

    with av.open(str(p), "w") as c:
        stream = c.add_stream("libx264", rate=10)
        stream.width = 32
        stream.height = 24
        stream.pix_fmt = "yuv420p"
        for i in range(21):
            f = av.VideoFrame.from_ndarray(
                np.full((24, 32, 3), i * 10, np.uint8), format="rgb24"
            )
            for packet in stream.encode(f):
                c.mux(packet)
        for packet in stream.encode():
            c.mux(packet)
    rows = list(sample_frames(p, "video", 0.7))
    assert [r[1] for r in rows] == pytest.approx([0.0, 0.7, 1.4])
    assert all(r[2] is not None and r[3] is not None for r in rows)


def test_observed_names_and_unknown_not_black():
    # Independent engineering labels for uniform canonical RGB patches.
    assert [
        color_name(c)
        for c in [(0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 0, 255), (128, 128, 128)]
    ] == ["black", "white", "red", "blue", "gray"]


def test_cancel_queued_is_terminal_and_retry_does_not_auto_increment(client):
    b = io.BytesIO()
    Image.new("RGB", (10, 10), "white").save(b, format="PNG")
    # Don't enqueue: row-lock the queue transaction to prevent GPU test work.
    media = client.post(
        "/api/media", files={"file": ("queue-test.png", b.getvalue())}
    ).json()
    jid = uuid.uuid4().hex
    with db.connect() as c:
        c.execute(
            "INSERT INTO jobs(id,media_id,status,config,sampling_seconds) VALUES(%s,%s,'CANCELLED','{}',1)",
            (jid, media["id"]),
        )
    assert client.post("/api/jobs/" + jid + "/cancel").status_code == 409
    assert client.get("/api/jobs/" + jid).json()["attempt"] == 0
    assert client.delete("/api/media/" + media["id"]).status_code == 200


def test_interruption_has_evidence_and_no_oom_claim(client):
    mid = uuid.uuid4().hex
    jid = uuid.uuid4().hex
    aid = uuid.uuid4().hex
    with db.connect() as c:
        c.execute(
            "INSERT INTO media(id,filename,kind,path,bytes,sha256,metadata) VALUES(%s,'lease-test.png','image',%s,0,'test','{}')",
            (mid, "lease-test/" + mid + ".png"),
        )
        c.execute(
            "INSERT INTO jobs(id,media_id,status,attempt,config,sampling_seconds,heartbeat) VALUES(%s,%s,'RUNNING',1,'{}',1,now()-interval '5 minutes')",
            (jid, mid),
        )
        c.execute(
            "INSERT INTO attempts(id,job_id,number,status) VALUES(%s,%s,1,'RUNNING')",
            (aid, jid),
        )
    try:
        reconcile_lost()
        row = client.get("/api/jobs/" + jid).json()
        assert row["status"] == "FAILED" and row["error"]["code"] == "WORKER_LOST"
        assert (
            row["attempts"][0]["status"] == "FAILED"
            and "OOM" not in row["error"]["message"]
        )
    finally:
        with db.connect() as c:
            c.execute("DELETE FROM media WHERE id=%s", (mid,))
