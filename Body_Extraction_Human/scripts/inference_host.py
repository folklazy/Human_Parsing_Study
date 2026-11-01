"""Private JSON-line IPC host. Real models only, isolated original environments.

Library output is not IPC: responses are prefixed @@BODY@@. One process per role,
no hidden retries, model changes or fallback. No database/server imports here.
"""

from pathlib import Path
import argparse, hashlib, json, os, sys, traceback, threading, time, subprocess
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
W = Path(os.getenv("BODY_WORKSPACE", P.parent)).resolve()
sys.path[:0] = [
    str(W / "CCTV_Human_Parsing_Benchmark/scripts"),
    str(W / "Human_Parsing_Benchmark/src"),
]


def sha(p):
    d = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(8 * 1024**2), b""):
            d.update(b)
    return d.hexdigest()


def atomic_json(p, value):
    p = Path(p)
    t = p.with_suffix(".tmp")
    t.write_text(json.dumps(value, allow_nan=False))
    os.replace(t, p)


HOST_SOURCE_SHA = sha(__file__)


class Host:
    def __init__(self, role):
        self.role = role
        self.loaded = False

    def initialize(self, r):
        if r.get("expected_source_sha256") != HOST_SOURCE_SHA:
            raise RuntimeError("APPLICATION_SOURCE_DRIFT")
        import torch

        self.torch = torch
        torch.set_num_threads(2)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        self.device = r["device"]
        self.parser = r["parser"]
        self.config = r
        if self.device.startswith("cuda"):
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA_UNAVAILABLE: no CPU fallback")
            free, _ = torch.cuda.mem_get_info()
            minimum = (
                7 * 2**30
                if self.role == "parser" and self.parser == "sapiens2_1b"
                else 1024**3
            )
            if self.role != "color" and free < minimum:
                raise RuntimeError("GPU_FREE_MEMORY_GUARD")
        parent = json.loads((P / "configs/MODEL_BINDINGS.json").read_text())
        if self.role == "detector":
            from ultralytics import YOLO

            checkpoint = W / parent["YOLO"]["checkpoint"]
            if sha(checkpoint) != parent["YOLO"]["checkpoint_sha256"]:
                raise ValueError("YOLO_CHECKPOINT_HASH_MISMATCH")
            self.model = YOLO(str(checkpoint))
            self.spec = parent["YOLO"]
            self.identity = dict(
                model="YOLO26x-Seg",
                sha256=parent["YOLO"]["checkpoint_sha256"],
                settings=self.spec,
            )
        elif self.role == "parser":
            mid = (
                "Sapiens2_1b"
                if self.parser == "sapiens2_1b"
                else "QANet_CIHP_HRNetW48_512x384"
            )
            self.spec = parent["models"][mid]
            revision = subprocess.check_output(
                ["git", "-C", str(W / self.spec["source"]), "rev-parse", "HEAD"],
                text=True,
            ).strip()
            if revision != self.spec["source_commit"]:
                raise ValueError("PARSER_SOURCE_REVISION_MISMATCH")
            if sha(W / self.spec["checkpoint"]) != self.spec["checkpoint_sha256"]:
                raise ValueError("PARSER_CHECKPOINT_HASH_MISMATCH")
            if sha(W / self.spec["native_config"]) != self.spec["native_config_sha256"]:
                raise ValueError("PARSER_CONFIG_HASH_MISMATCH")
            if self.parser == "sapiens2_1b":
                from sapiens.dense.models import init_model
                from safetensors.torch import load_file

                self.model = init_model(
                    W / self.spec["native_config"], checkpoint=None, device="cpu"
                )
                state = load_file(W / self.spec["checkpoint"], device="cpu")
                self.model.load_state_dict(state, strict=True)
                del state
                self.model.float().eval().to(self.device)
                self.classes = 29
            else:
                if not self.device.startswith("cuda"):
                    raise ValueError("QANet original adapter is CUDA-only")
                from controlled_roi_models import CropModel

                self.adapter = CropModel(
                    W, self.spec, Path(r["runtime_path"]) / "qanet"
                )
                self.model = self.adapter.model
                self.classes = 20
            self.identity = dict(
                model=mid,
                checkpoint_sha256=self.spec["checkpoint_sha256"],
                config_sha256=self.spec["native_config_sha256"],
                source_revision=self.spec["source_commit"],
                route="CONTROLLED_YOLO_PERSON_ROI",
                precision="FP32",
                classes=self.classes,
            )
        else:
            color = Path(r["color_source"])
            sys.path.insert(0, str(color / "src"))
            from garment_color.learned import LearnedColorPredictor
            from garment_color.preprocessor import MaskPreprocessor
            from garment_color.features import extract_features

            self.learned = LearnedColorPredictor(
                color / "outputs/t4-pilot-20261101/learned_color.pt",
                device="cpu",
                expected_sha256="4145b416f9020422e389210af6eab6adc6d92d6c37af6033f60ffc712969bfde",
            )
            self.preprocess = MaskPreprocessor()
            self.extract_features = extract_features
            self.identity = dict(
                model="T4_MLP_62_64_32_12_v1",
                device="cpu",
                calibrated=False,
                checkpoint_sha256="4145b416f9020422e389210af6eab6adc6d92d6c37af6033f60ffc712969bfde",
            )
        self.identity.update(
            host_source_sha256=HOST_SOURCE_SHA,
            python=sys.version,
            torch=torch.__version__,
            device=self.device if self.role != "color" else "cpu",
            GPU=torch.cuda.get_device_name(0)
            if self.device.startswith("cuda")
            else None,
        )
        self.loaded = True
        return self.identity

    def run(self, r):
        if r["op"] == "init":
            return self.initialize(r)
        if not self.loaded:
            raise RuntimeError("MODEL_NOT_INITIALIZED")
        rgb = np.asarray(Image.open(r["image"]).convert("RGB"))
        root = Path(r["out"])
        root.mkdir(parents=True, exist_ok=True)
        if self.role == "detector":
            with self.torch.inference_mode():
                result = self.model.predict(
                    rgb[:, :, ::-1].copy(),
                    device=self.device,
                    classes=[0],
                    imgsz=640,
                    conf=0.25,
                    iou=0.7,
                    max_det=200,
                    retina_masks=True,
                    half=False,
                    augment=False,
                    verbose=False,
                    save=False,
                )[0]
            h, w = rgb.shape[:2]
            boxes = result.boxes.xyxy.cpu().numpy()
            scores = result.boxes.conf.cpu().numpy()
            if len(boxes) and result.masks is None:
                raise ValueError("DETECTOR_MISSING_INSTANCE_MASK")
            masks = (
                result.masks.data.cpu().numpy() > 0.5
                if len(boxes)
                else np.empty((0, h, w), bool)
            )
            if (
                masks.shape != (len(boxes), h, w)
                or not np.isfinite(boxes).all()
                or not np.isfinite(scores).all()
            ):
                raise ValueError("DETECTOR_GEOMETRY_CONTRACT")
            if any(not m.any() for m in masks):
                raise ValueError("DETECTOR_EMPTY_INSTANCE_MASK")
            path = root / "detector.npz"
            np.savez_compressed(path, masks=masks, boxes=boxes, scores=scores)
            return dict(
                path=str(path), people=len(boxes), sha256=sha(path), original_wh=[w, h]
            )
        if self.role == "parser":
            from sapiens_input_variants import detector_crop

            with np.load(r["detector"], allow_pickle=False) as a:
                extent = a["masks"][r["ordinal"]]
                box = a["boxes"][r["ordinal"]]
            crop, xyxy = detector_crop(rgb, box, extent, 0.1)
            x0, y0, x1, y1 = xyxy
            if self.parser == "sapiens2_1b":
                from sapiens_input_variants import letterbox, restore_letterbox

                t, g, _ = letterbox(crop, self.model.data_preprocessor)
                with self.torch.inference_mode():
                    out = self.model(t.to(self.device))
                native = restore_letterbox(out, g)
                del out, t
            else:
                native, _, details = self.adapter.infer(
                    crop,
                    Path(r["image"]),
                    [
                        float(box[0] - x0),
                        float(box[1] - y0),
                        float(box[2] - x0),
                        float(box[3] - y0),
                    ],
                )
                g = details.get("input_geometry", details)
            if (
                native.shape != crop.shape[:2]
                or native.dtype != np.uint8
                or np.any(native >= self.classes)
            ):
                raise ValueError("PARSING_LABEL_GEOMETRY_CONTRACT")
            raw = np.zeros(extent.shape, np.uint8)
            raw[y0:y1, x0:x1] = native
            owned = np.where(extent, raw, 0).astype(np.uint8)
            Image.fromarray(crop).save(root / "crop.png")
            Image.fromarray(owned).save(root / "native.png")
            mask_rgba = np.zeros((*extent.shape, 4), np.uint8)
            mask_rgba[extent] = [30, 160, 190, 150]
            Image.fromarray(mask_rgba).save(root / "instance.png")
            overlay = np.zeros_like(mask_rgba)
            targets = (
                {
                    "Hair": [4],
                    "Face (includes Neck)": [3, 24, 25, 26, 27, 28],
                    "Upper": [23],
                    "Lower": [13],
                }
                if self.classes == 29
                else {"Hair": [2], "Face": [13], "Upper": [5, 7], "Lower": [9, 12]}
            )
            colors = [
                [40, 200, 255, 210],
                [255, 210, 30, 210],
                [40, 220, 90, 210],
                [240, 70, 210, 210],
            ]
            for ids, col in zip(targets.values(), colors):
                overlay[np.isin(owned, ids)] = col
            Image.fromarray(overlay).save(root / "parsing.png")
            return dict(
                crop_xyxy=xyxy,
                input_geometry=g,
                original_wh=[rgb.shape[1], rgb.shape[0]],
                native_classes=self.classes,
                output_labels=np.unique(owned).tolist(),
                native_sha256=sha(root / "native.png"),
                targets=targets,
            )
        native = np.asarray(Image.open(r["native"]))
        return self.color(rgb, native)

    def color(self, rgb, native):
        from color_contract import observed_palette

        sapiens = self.parser == "sapiens2_1b"
        results = {}
        types = []
        specs = (
            {
                "upper": [(23, "upper_clothing", (5, 7))],
                "lower": [(13, "lower_clothing", (9, 12))],
            }
            if sapiens
            else {
                "upper": [(5, "upper_clothing", (5,)), (7, "coat", (7,))],
                "lower": [(9, "pants", (9,)), (12, "skirt", (12,))],
            }
        )
        for region, groups in specs.items():
            regionmask = np.isin(native, [row[0] for row in groups])
            pixels = self.preprocess.extract_clean_pixels(rgb, regionmask)
            base = dict(
                status="unknown",
                reason="พื้นที่เสื้อผ้าไม่พอหรือถูกบดบัง",
                colors=[],
                palette=[],
                learned=None,
                pixels=int(regionmask.sum()),
                algorithm="T4_MLP_62_64_32_12_v1 + observed palette",
                calibrated_confidence=None,
            )
            if len(pixels) < 40:
                results[region] = base
                continue
            # Original RGB only. Palette is a separately named observed-color diagnostic.
            features = self.extract_features(pixels)
            palette = observed_palette(features.clusters)
            hypotheses = []
            for label, name, categories in groups:
                mask = native == label
                if int(mask.sum()) < 40:
                    continue
                types.append(name)
                pp = self.preprocess.extract_clean_pixels(rgb, mask)
                hypotheses.extend(
                    dict(native_category=c, **self.learned.predict_pixels(pp, c))
                    for c in categories
                )
            ids = [r["color_id"] for r in hypotheses]
            agreement = bool(ids) and len(set(ids)) == 1
            base.update(
                status="observed",
                reason=None,
                colors=[p["name"] for p in palette if p["fraction"] >= 0.15][:2],
                palette=palette,
                learned=dict(
                    category_hypotheses=hypotheses,
                    color_id=ids[0] if agreement else None,
                    status="category_agreement"
                    if agreement
                    else "category_or_layer_ambiguous",
                    note="Sapiens generic category does not prove coat/pants/skirt; no forced category substitution",
                ),
                pixels=len(pixels),
                quality="observed_pixels_not_accuracy_probability",
            )
            # Near-grayscale/IR: hue cannot be established; neutral appearance is retained.
            if (
                float(
                    np.median(
                        np.max(pixels, axis=1).astype(float) - np.min(pixels, axis=1)
                    )
                )
                < 4
            ):
                base["warnings"] = [
                    "ภาพเกือบไม่มีสี: บอกได้เฉพาะลักษณะที่เห็น ไม่ใช่สีจริงภายใต้แสงปกติ"
                ]
            results[region] = base
        results["garment_types"] = sorted(set(types))
        return results


if __name__ == "__main__":
    parent = os.getppid()

    def parent_watch():
        while True:
            time.sleep(2)
            if os.getppid() != parent:
                os._exit(72)

    threading.Thread(target=parent_watch, daemon=True).start()
    p = argparse.ArgumentParser()
    p.add_argument("--role", choices=["detector", "parser", "color"], required=True)
    args = p.parse_args()
    host = Host(args.role)
    for line in sys.stdin:
        try:
            reply = dict(ok=True, result=host.run(json.loads(line)))
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            reply = dict(ok=False, error_type=type(exc).__name__, error=str(exc)[:1000])
        print(
            "@@BODY@@" + json.dumps(reply, ensure_ascii=False, allow_nan=False),
            flush=True,
        )
