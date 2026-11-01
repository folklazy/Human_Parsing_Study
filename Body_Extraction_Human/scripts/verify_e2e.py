"""Actual upload -> worker inference -> DB -> AND search -> deep-link checks.

Inputs are fresh transforms, never cached predictions. Private inputs/artifacts
and per-person output stay in .runtime/storage; sanitized report has counts only.
"""

from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys, time, os
import httpx, numpy as np, av
from PIL import Image, ImageOps, ImageDraw

P = Path(__file__).resolve().parents[1]
W = P.parent
sys.path.insert(0, str(P / "backend"))
from app import settings as s


def main():
    out = P / ".runtime/verification"
    out.mkdir(exist_ok=True)
    original = Image.open(W / "datasets/CIHP/Training/Images/0000930.jpg").convert(
        "RGB"
    )
    rgb = Image.new("RGB", (original.width + 60, original.height + 40), "#c7d0d6")
    rgb.paste(ImageOps.mirror(original), (30, 20))
    rgb.save(out / "multi.png")
    blank = Image.new("RGB", (640, 400), "#eeeeee")
    blank.save(out / "empty.png")
    occluded = rgb.copy()
    d = ImageDraw.Draw(occluded)
    d.rectangle((0, rgb.height * 0.58, rgb.width, rgb.height), fill="#899eac")
    occluded.save(out / "occluded.png")
    with av.open(str(out / "clip.mp4"), "w") as container:
        stream = container.add_stream("libx264", rate=10)
        stream.width = rgb.width
        stream.height = rgb.height
        stream.pix_fmt = "yuv420p"
        for i in range(21):
            image = rgb if i < 10 else ImageOps.mirror(rgb)
            frame = av.VideoFrame.from_image(image)
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    c = httpx.Client(
        base_url="http://127.0.0.1:8038",
        timeout=180,
        headers={"X-Requested-With": "BodyExtraction"},
    )
    r = c.post("/api/login", json=dict(username=s.USERNAME, password=s.PASSWORD))
    r.raise_for_status()
    result = dict(
        started_utc=datetime.now(timezone.utc).isoformat(),
        model=s.PARSER,
        inputs="fresh transformations of an existing research image + blank + freshly encoded MP4; no saved predictions",
        cases={},
    )
    for name in ["multi.png", "empty.png", "occluded.png", "clip.mp4"]:
        with (out / name).open("rb") as f:
            r = c.post(
                "/api/media",
                files={"file": (name, f)},
                data={
                    "source": "Application verification",
                    "event_start": "2026-11-01T10:00:00+07:00",
                },
            )
            r.raise_for_status()
            media = r.json()
        r = c.post("/api/jobs", json=dict(media_id=media["id"], sampling_seconds=1))
        r.raise_for_status()
        job = r.json()
        result["cases"][name] = dict(
            job_id=job["id"],
            media_id=media["id"],
            input_sha256=hashlib.sha256((out / name).read_bytes()).hexdigest(),
            status="QUEUED",
        )
    (out / "RUNNING.json").write_text(json.dumps(result, indent=2))
    deadline = time.monotonic() + 2400
    while time.monotonic() < deadline:
        unfinished = False
        for name, row in result["cases"].items():
            r = c.get("/api/jobs/" + row["job_id"])
            r.raise_for_status()
            job = r.json()
            row.update(
                status=job["status"],
                frames=job["completed_frames"],
                people=job["processed_people"],
                error=job["error"],
            )
            if job["status"] in ("RUNNING", "QUEUED"):
                unfinished = True
        (out / "RUNNING.json").write_text(json.dumps(result, indent=2))
        if not unfinished:
            break
        time.sleep(5)
    result["decode_invalid_status"] = c.post(
        "/api/media", files={"file": ("broken.png", b"not an image")}
    ).status_code
    result["unsupported_status"] = c.post(
        "/api/media", files={"file": ("file.txt", b"hello")}
    ).status_code
    result["anonymous_asset_status"] = httpx.get(
        "http://127.0.0.1:8038/api/files/uploads/not-real/original.png"
    ).status_code
    matches = []
    for name, row in result["cases"].items():
        job = c.get("/api/jobs/" + row["job_id"]).json()
        row["timestamps"] = [f["timestamp_seconds"] for f in job["frames"]]
        for frame in job["frames"]:
            detail = c.get("/api/frames/" + frame["id"]).json()
            for person in detail["persons"]:
                if person["upper_colors"] and person["lower_colors"]:
                    upper, lower = person["upper_colors"][0], person["lower_colors"][0]
                    found = c.get(
                        "/api/search",
                        params={
                            "upper": upper,
                            "lower": lower,
                            "q": "Application verification",
                            "page_size": 60,
                        },
                    ).json()
                    assert any(
                        p["id"] == person["id"]
                        and p["frame_id"] == frame["id"]
                        and p["job_id"] == job["id"]
                        for p in found["items"]
                    )
                    assert all(
                        upper in p["upper_colors"] and lower in p["lower_colors"]
                        for p in found["items"]
                    )
                    matches.append(
                        dict(
                            person=person["id"],
                            frame=frame["id"],
                            job=job["id"],
                            upper=upper,
                            lower=lower,
                        )
                    )
                    break
    result["AND_search_link_checks"] = len(matches)
    result["example_deep_link"] = matches[0] if matches else None
    result["finished_utc"] = datetime.now(timezone.utc).isoformat()
    result["all_inference_cases_success"] = all(
        r["status"] == "SUCCEEDED" for r in result["cases"].values()
    )
    (out / "RESULTS.json").write_text(json.dumps(result, indent=2))
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("cases", "example_deep_link")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
