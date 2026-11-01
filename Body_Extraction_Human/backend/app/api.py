from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict, deque
from urllib.parse import urlparse
import hashlib, hmac, json, shutil, time, uuid
from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    UploadFile,
    File,
    Form,
    Depends,
    Query,
)
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from psycopg.types.json import Jsonb
from . import settings as s, db
from .media import inspect_media


@asynccontextmanager
async def lifespan(app):
    if len(s.SECRET) < 32 or len(s.PASSWORD) < 12 or not s.DB_URL:
        raise RuntimeError(
            "Configure DATABASE_URL, BODY_SECRET and BODY_PASSWORD in private .env"
        )
    db.migrate()
    yield


app = FastAPI(
    title="Body Extraction Human API",
    version="1.0.0",
    lifespan=lifespan,
    description="Authenticated image/video clothing appearance search. No identity recognition or cross-frame tracking.",
)
signer = URLSafeTimedSerializer(s.SECRET or "unconfigured", salt="body-session-v1")
login_attempts = defaultdict(deque)


def authenticated(request: Request):
    try:
        value = signer.loads(request.cookies.get("body_session", ""), max_age=43200)
        if value["user"] != s.USERNAME:
            raise BadSignature("user")
    except (BadSignature, SignatureExpired, KeyError):
        raise HTTPException(401, "กรุณาเข้าสู่ระบบ")
    return value["user"]


@app.middleware("http")
async def request_security(request, call_next):
    if request.url.path == "/api/media" and request.method == "POST":
        limit = s.MAX_UPLOAD + 1024**2
        try:
            if int(request.headers.get("content-length", "0")) > limit:
                return JSONResponse({"detail": "ไฟล์มีขนาดเกินขีดจำกัด"}, 413)
        except ValueError:
            return JSONResponse({"detail": "Invalid Content-Length"}, 400)
        received = 0
        original_receive = request._receive

        async def bounded_receive():
            nonlocal received
            message = await original_receive()
            received += len(message.get("body", b""))
            if received > limit:
                request.state.upload_too_large = True
                raise HTTPException(413, "ไฟล์มีขนาดเกินขีดจำกัด")
            return message

        request._receive = bounded_receive
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("origin")
        if origin and urlparse(origin).netloc != request.headers.get("host"):
            return JSONResponse({"detail": "Cross-origin mutation rejected"}, 403)
        if (
            request.url.path != "/api/login"
            and request.headers.get("x-requested-with") != "BodyExtraction"
        ):
            return JSONResponse({"detail": "Missing CSRF request header"}, 403)
    response = await call_next(request)
    if getattr(request.state, "upload_too_large", False):
        return JSONResponse({"detail": "ไฟล์มีขนาดเกินขีดจำกัด"}, 413)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


class Login(BaseModel):
    username: str
    password: str


@app.post("/api/login")
def login(body: Login, request: Request):
    key = request.client.host if request.client else "local"
    q = login_attempts[key]
    now = time.monotonic()
    while q and q[0] < now - 60:
        q.popleft()
    if len(q) >= 8:
        raise HTTPException(429, "ลองเข้าสู่ระบบบ่อยเกินไป กรุณารอหนึ่งนาที")
    q.append(now)
    if not (
        hmac.compare_digest(body.username, s.USERNAME)
        and hmac.compare_digest(body.password, s.PASSWORD)
    ):
        raise HTTPException(401, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    response = JSONResponse({"username": s.USERNAME})
    response.set_cookie(
        "body_session",
        signer.dumps({"user": s.USERNAME, "nonce": uuid.uuid4().hex}),
        httponly=True,
        secure=s.COOKIE_SECURE,
        samesite="strict",
        max_age=43200,
    )
    return response


@app.get("/api/me")
def me(user=Depends(authenticated)):
    return {"username": user}


@app.post("/api/logout")
def logout(user=Depends(authenticated)):
    r = JSONResponse({"ok": True})
    r.delete_cookie("body_session")
    return r


@app.get("/api/health")
def health():
    try:
        db.one("SELECT 1")
        return {"status": "ok"}
    except Exception:
        return JSONResponse({"status": "database_unavailable"}, 503)


@app.get("/api/ready")
def ready(user=Depends(authenticated)):
    paths = {
        "YOLO weights": s.YOLO_CHECKPOINT,
        "color checkpoint": s.COLOR_CHECKPOINT,
        "color source": s.COLOR_SOURCE / "src/garment_color/learned.py",
        "YOLO environment": s.ENV_YOLO,
        "parser environment": s.ENV_SAPIENS
        if s.PARSER == "sapiens2_1b"
        else s.ENV_QANET,
    }
    paths["parser weights"] = s.WORKSPACE / (
        "models/human_parsing/sapiens2/1b/sapiens2_1b_seg.safetensors"
        if s.PARSER == "sapiens2_1b"
        else json.loads((s.PROJECT / "configs/MODEL_BINDINGS.json").read_text())[
            "models"
        ]["QANet_CIHP_HRNetW48_512x384"]["checkpoint"]
    )
    missing = [k for k, p in paths.items() if not p.exists()]
    worker_record = {}
    try:
        worker_record = json.loads(
            (s.PROJECT / ".runtime/services.json").read_text()
        ).get("worker", {})
        worker_record["running"] = (
            "app.worker"
            in (Path("/proc") / str(worker_record["pid"]) / "cmdline")
            .read_bytes()
            .decode()
        )
    except (OSError, KeyError, ValueError):
        worker_record = {"running": False}
    return dict(
        ready=not missing,
        missing=missing,
        worker_process=worker_record,
        config=s.config_snapshot(),
        limits=dict(
            max_upload_bytes=s.MAX_UPLOAD,
            max_video_seconds=s.MAX_VIDEO_SECONDS,
            max_sampled_frames=s.MAX_SAMPLED_FRAMES,
        ),
        free_disk_gib=round(shutil.disk_usage(s.STORAGE).free / 2**30, 1),
        license_notice="Sapiens2 prohibits surveillance, including surveillance research. Use only within the model license; QANet is a separate selectable configuration."
        if s.PARSER == "sapiens2_1b"
        else "QANet source MIT; YOLO AGPL-3.0/enterprise. Check weight terms for intended use.",
        supported_garments=["upper_clothing", "lower_clothing"]
        if s.PARSER == "sapiens2_1b"
        else ["upper_clothing", "coat", "pants", "skirt"],
        worker=db.one(
            "SELECT worker,heartbeat FROM jobs WHERE heartbeat IS NOT NULL ORDER BY heartbeat DESC LIMIT 1"
        ),
        model_loaded=False,
        readiness_scope="asset presence only; worker/model errors remain explicit",
    )


@app.post("/api/media", status_code=201)
async def upload(
    file: UploadFile = File(...),
    source: str = Form(""),
    event_start: str | None = Form(None),
    user=Depends(authenticated),
):
    filename = Path((file.filename or "").replace("\\", "/")).name[:200]
    suffix = Path(filename).suffix.lower()
    if suffix not in (".jpg", ".jpeg", ".png", ".mp4"):
        raise HTTPException(415, "รองรับ JPG, PNG และ MP4 เท่านั้น")
    if shutil.disk_usage(s.STORAGE).free < s.MIN_DISK_GIB * 2**30:
        raise HTTPException(507, "พื้นที่ว่างต่ำกว่าเกณฑ์")
    start = None
    if event_start:
        try:
            start = datetime.fromisoformat(event_start.replace("Z", "+00:00"))
            if start.tzinfo is None:
                raise ValueError("timezone required")
        except ValueError:
            raise HTTPException(422, "เวลาเริ่มคลิปต้องระบุ timezone เช่น +07:00")
    mid = uuid.uuid4().hex
    directory = s.STORAGE / "uploads" / mid
    directory.mkdir(parents=True)
    path = directory / ("original" + suffix)
    size = 0
    digest = hashlib.sha256()
    try:
        with path.open("xb") as f:
            while chunk := await file.read(1024**2):
                size += len(chunk)
                if size > s.MAX_UPLOAD:
                    raise HTTPException(413, "ไฟล์มีขนาดเกินขีดจำกัด")
                digest.update(chunk)
                f.write(chunk)
        if not size:
            raise ValueError("ไฟล์ว่าง")
        kind, metadata = inspect_media(path, suffix)
        rel = str(path.relative_to(s.STORAGE))
        with db.connect() as c:
            row = c.execute(
                "INSERT INTO media(id,filename,source,kind,path,bytes,sha256,metadata,event_start) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
                (
                    mid,
                    filename,
                    source[:200],
                    kind,
                    rel,
                    size,
                    digest.hexdigest(),
                    Jsonb(metadata),
                    start,
                ),
            ).fetchone()
        return row
    except HTTPException:
        shutil.rmtree(directory)
        raise
    except Exception as exc:
        shutil.rmtree(directory)
        raise HTTPException(422, "เปิดไฟล์ไม่ได้ หรือไฟล์ไม่ถูกต้อง: " + str(exc)[:250])
    finally:
        await file.close()


class JobRequest(BaseModel):
    media_id: str
    sampling_seconds: float = Field(default=1, ge=0.2, le=3600)


@app.post("/api/jobs", status_code=201)
def create_job(body: JobRequest, user=Depends(authenticated)):
    media = db.one("SELECT * FROM media WHERE id=%s", (body.media_id,))
    if not media:
        raise HTTPException(404, "ไม่พบไฟล์")
    duration = media["metadata"].get("duration_seconds")
    if (
        media["kind"] == "video"
        and duration
        and duration / body.sampling_seconds > s.MAX_SAMPLED_FRAMES
    ):
        raise HTTPException(422, "จำนวนเฟรมตามช่วงเวลาที่เลือกเกินขีดจำกัด")
    with db.connect() as c:
        c.execute("SELECT id FROM media WHERE id=%s FOR UPDATE", (body.media_id,))
        active = c.execute(
            "SELECT id FROM jobs WHERE media_id=%s AND status IN ('QUEUED','RUNNING')",
            (body.media_id,),
        ).fetchone()
        if active:
            raise HTTPException(409, "ไฟล์นี้มีงานที่ยังไม่จบ")
        return c.execute(
            "INSERT INTO jobs(id,media_id,config,sampling_seconds) VALUES(%s,%s,%s,%s) RETURNING *",
            (
                uuid.uuid4().hex,
                body.media_id,
                Jsonb(s.config_snapshot()),
                body.sampling_seconds,
            ),
        ).fetchone()


@app.get("/api/jobs")
def jobs(page: int = Query(1, ge=1), user=Depends(authenticated)):
    return dict(
        items=db.all_rows(
            "SELECT j.*,m.filename,m.source,m.kind FROM jobs j JOIN media m ON m.id=j.media_id ORDER BY j.created_at DESC LIMIT 20 OFFSET %s",
            ((page - 1) * 20,),
        ),
        total=db.one("SELECT count(*) n FROM jobs")["n"],
        page=page,
    )


def get_job(jid):
    row = db.one(
        "SELECT j.*,m.filename,m.source,m.kind,m.path media_path,m.event_start,m.uploaded_at,m.metadata media_metadata FROM jobs j JOIN media m ON m.id=j.media_id WHERE j.id=%s",
        (jid,),
    )
    if not row:
        raise HTTPException(404, "ไม่พบงาน")
    return row


@app.get("/api/jobs/{jid}")
def job_detail(jid: str, user=Depends(authenticated)):
    row = get_job(jid)
    row["frames"] = db.all_rows(
        "SELECT f.*,(SELECT count(*) FROM persons p WHERE p.frame_id=f.id) people FROM frames f WHERE job_id=%s AND attempt=%s ORDER BY sample_index",
        (jid, row["attempt"]),
    )
    if row["status"] == "QUEUED":
        row["frames"] = []
    row["attempts"] = db.all_rows(
        "SELECT * FROM attempts WHERE job_id=%s ORDER BY number", (jid,)
    )
    row["partial"] = row["status"] != "SUCCEEDED" and bool(row["frames"])
    return row


@app.get("/api/frames/{fid}")
def frame_detail(fid: str, user=Depends(authenticated)):
    row = db.one(
        "SELECT f.*,j.status job_status,m.event_start FROM frames f JOIN jobs j ON j.id=f.job_id JOIN media m ON m.id=j.media_id WHERE f.id=%s",
        (fid,),
    )
    if not row:
        raise HTTPException(404, "ไม่พบเฟรม")
    row["persons"] = db.all_rows(
        "SELECT * FROM persons WHERE frame_id=%s ORDER BY ordinal", (fid,)
    )
    return row


@app.post("/api/jobs/{jid}/cancel")
def cancel(jid: str, user=Depends(authenticated)):
    with db.connect() as c:
        row = c.execute(
            "UPDATE jobs SET cancel_requested=true,status=CASE WHEN status='QUEUED' THEN 'CANCELLED' ELSE status END WHERE id=%s AND status IN ('QUEUED','RUNNING') RETURNING *",
            (jid,),
        ).fetchone()
    if not row:
        raise HTTPException(409, "สถานะนี้ยกเลิกไม่ได้")
    return row


@app.post("/api/jobs/{jid}/retry")
def retry(jid: str, user=Depends(authenticated)):
    with db.connect() as c:
        row = c.execute(
            "UPDATE jobs SET status='QUEUED',cancel_requested=false,error=NULL,completed_frames=0,total_frames=NULL,processed_people=0,last_timestamp=NULL,finished_at=NULL WHERE id=%s AND status IN ('FAILED','CANCELLED') RETURNING *",
            (jid,),
        ).fetchone()
    if not row:
        raise HTTPException(409, "ลองใหม่ได้เฉพาะงานล้มเหลวหรือยกเลิกแล้ว")
    return row


@app.delete("/api/media/{mid}")
def delete_media(mid: str, user=Depends(authenticated)):
    with db.connect() as c:
        media = c.execute(
            "SELECT * FROM media WHERE id=%s FOR UPDATE", (mid,)
        ).fetchone()
        if not media:
            raise HTTPException(404, "ไม่พบไฟล์")
        rows = c.execute(
            "SELECT id,status FROM jobs WHERE media_id=%s FOR UPDATE", (mid,)
        ).fetchall()
        if any(r["status"] == "RUNNING" for r in rows):
            raise HTTPException(409, "กรุณายกเลิกงานและรอให้ worker หยุดก่อนลบ")
        c.execute("DELETE FROM media WHERE id=%s", (mid,))
    for row in rows:
        shutil.rmtree(s.STORAGE / "jobs" / row["id"], ignore_errors=True)
    shutil.rmtree((s.STORAGE / media["path"]).parent, ignore_errors=True)
    return {"deleted": True}


@app.get("/api/search")
def search(
    upper: str | None = None,
    lower: str | None = None,
    garment: str | None = None,
    kind: str | None = None,
    q: str | None = None,
    uploaded_from: datetime | None = None,
    uploaded_to: datetime | None = None,
    event_from: datetime | None = None,
    event_to: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(18, ge=1, le=60),
    user=Depends(authenticated),
):
    where = ["j.status='SUCCEEDED'", "f.attempt=j.attempt"]
    args = []
    for value, column in [
        (upper, "p.upper_colors"),
        (lower, "p.lower_colors"),
        (garment, "p.garment_types"),
    ]:
        if value:
            where.append(f"%s=ANY({column})")
            args.append(value)
    if kind:
        where.append("m.kind=%s")
        args.append(kind)
    if q:
        where.append("(m.filename ILIKE %s OR m.source ILIKE %s)")
        args.extend(["%" + q + "%"] * 2)
    for value, column, op in [
        (uploaded_from, "m.uploaded_at", ">="),
        (uploaded_to, "m.uploaded_at", "<"),
        (event_from, "(m.event_start+f.timestamp_seconds*interval '1 second')", ">="),
        (event_to, "(m.event_start+f.timestamp_seconds*interval '1 second')", "<"),
    ]:
        if value:
            if value.tzinfo is None:
                raise HTTPException(422, "Date filters require timezone")
            where.append(column + op + "%s")
            args.append(value)
    base = (
        " FROM persons p JOIN frames f ON f.id=p.frame_id JOIN jobs j ON j.id=f.job_id JOIN media m ON m.id=j.media_id WHERE "
        + " AND ".join(where)
    )
    total = db.one("SELECT count(*) n" + base, tuple(args))["n"]
    rows = db.all_rows(
        "SELECT p.*,f.job_id,f.timestamp_seconds,f.id frame_id,m.filename,m.source,m.kind,m.event_start"
        + base
        + " ORDER BY j.created_at DESC,f.sample_index,p.ordinal LIMIT %s OFFSET %s",
        tuple(args + [page_size, (page - 1) * page_size]),
    )
    return dict(
        items=rows,
        total=total,
        page=page,
        page_size=page_size,
        search_scope="completed current attempts; colors on same person; observed dominant/secondary palette labels",
    )


@app.get("/api/files/{asset:path}")
def asset_file(asset: str, user=Depends(authenticated)):
    path = (s.STORAGE / asset).resolve()
    if (
        not path.is_relative_to(s.STORAGE)
        or not path.is_file()
        or path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".mp4")
    ):
        raise HTTPException(404, "ไม่พบไฟล์")
    return FileResponse(path)


frontend = s.PROJECT / "frontend/dist"
if frontend.exists():
    app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
