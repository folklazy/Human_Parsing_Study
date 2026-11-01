from pathlib import Path
import os, hashlib
from dotenv import load_dotenv

PROJECT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT / ".env")
load_dotenv(PROJECT / ".runtime/app.env")
WORKSPACE = Path(os.getenv("BODY_WORKSPACE", PROJECT.parent)).resolve()
STORAGE = Path(os.getenv("BODY_STORAGE", PROJECT / "storage")).resolve()
STORAGE.mkdir(parents=True, exist_ok=True)
DB_URL = os.environ.get("DATABASE_URL", "")
SECRET = os.environ.get("BODY_SECRET", "")
PASSWORD = os.environ.get("BODY_PASSWORD", "")
USERNAME = os.environ.get("BODY_USERNAME", "admin")
COOKIE_SECURE = os.getenv("BODY_COOKIE_SECURE", "false").lower() == "true"
MAX_UPLOAD = int(os.getenv("BODY_MAX_UPLOAD_MB", "500")) * 1024**2
MAX_PIXELS = int(os.getenv("BODY_MAX_PIXELS", "40000000"))
MIN_DISK_GIB = int(os.getenv("BODY_MIN_FREE_DISK_GIB", "20"))
MAX_VIDEO_SECONDS = int(os.getenv("BODY_MAX_VIDEO_SECONDS", "3600"))
MAX_SAMPLED_FRAMES = int(os.getenv("BODY_MAX_SAMPLED_FRAMES", "3600"))
MODEL_TIMEOUT = int(os.getenv("BODY_MODEL_TIMEOUT_SECONDS", "600"))
PARSER = os.getenv("BODY_PARSER", "sapiens2_1b")
if PARSER not in ("sapiens2_1b", "qanet"):
    raise ValueError("BODY_PARSER must be sapiens2_1b or qanet")
DEVICE = os.getenv("BODY_DEVICE", "cuda:0")
COLOR_SOURCE = Path(
    os.getenv("BODY_COLOR_SOURCE", WORKSPACE.parent / "Garment-Color-Extractor")
).resolve()
ENV_API = WORKSPACE / ".venvs/body-extraction-api/bin/python"
ENV_YOLO = WORKSPACE / ".venv/bin/python"
ENV_SAPIENS = WORKSPACE / ".venvs/sapiens2-pilot/bin/python"
ENV_QANET = WORKSPACE / ".venvs/parser-legacy-cu113/bin/python"
COLOR_CHECKPOINT = COLOR_SOURCE / "outputs/t4-pilot-20261101/learned_color.pt"
COLOR_SHA = "4145b416f9020422e389210af6eab6adc6d92d6c37af6033f60ffc712969bfde"
YOLO_CHECKPOINT = WORKSPACE / "models/yolo26x-seg.pt"
EXECUTION_SOURCES = [
    PROJECT / "scripts/inference_host.py",
    PROJECT / "scripts/color_contract.py",
    PROJECT / "configs/MODEL_BINDINGS.json",
    PROJECT / "backend/app/worker.py",
    PROJECT / "backend/app/media.py",
]
EXECUTION_HASHES = {
    str(p.relative_to(PROJECT)): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in EXECUTION_SOURCES
}


def config_snapshot():
    return dict(
        version="body-extraction-1",
        detector="YOLO26x-Seg",
        parser=PARSER,
        route="CONTROLLED_YOLO_PERSON_ROI",
        device=DEVICE,
        precision="FP32",
        batch_size=1,
        color_method="T4_MLP_62_64_32_12_v1",
        color_palette="observed_LAB_clusters_HSV_names_v1",
        detector_settings=dict(
            imgsz=640, conf=0.25, iou=0.7, max_det=200, retina_masks=True
        ),
        crop_context=0.1,
        ownership="detector-mask clipping",
        tracking=False,
        color_category_policy="CIHP native categories; Sapiens requires agreement over 5/7 or 9/12",
        unsupported_apparel="separate native class; no dress splitting",
        no_person="successful empty frame",
        retry="manual only; immutable attempts",
        execution_source_hashes=EXECUTION_HASHES,
    )
