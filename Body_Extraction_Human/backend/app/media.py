from pathlib import Path
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
import av
from . import settings as s


def inspect_media(path, suffix):
    if suffix in (".jpg", ".jpeg", ".png"):
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as im:
                if im.format not in ("JPEG", "PNG"):
                    raise ValueError("เนื้อหาไฟล์ไม่ใช่ JPG/PNG")
                if im.width * im.height > s.MAX_PIXELS:
                    raise ValueError("ภาพมีจำนวน pixels เกินขีดจำกัด")
                im.verify()
            with Image.open(path) as im:
                im = ImageOps.exif_transpose(im)
                return "image", dict(
                    width=im.width,
                    height=im.height,
                    duration_seconds=None,
                    orientation="EXIF transposed for processing",
                )
    if suffix != ".mp4":
        raise ValueError("รองรับ JPG, PNG และ MP4 เท่านั้น")
    with av.open(str(path)) as container:
        if not container.streams.video:
            raise ValueError("ไม่พบ video stream")
        stream = container.streams.video[0]
        if stream.width * stream.height > s.MAX_PIXELS:
            raise ValueError("ขนาดเฟรมเกินขีดจำกัด")
        duration = (
            float(stream.duration * stream.time_base)
            if stream.duration is not None
            else (
                float(container.duration / av.time_base) if container.duration else None
            )
        )
        if duration is not None and duration > s.MAX_VIDEO_SECONDS:
            raise ValueError("วิดีโอยาวเกินขีดจำกัด")
        first = next(container.decode(stream), None)
        if first is None or first.pts is None:
            raise ValueError("ไม่พบเฟรมที่มี timestamp ใช้งานได้")
        rotation = int(first.rotation)
        if rotation % 90:
            raise ValueError("ไม่รองรับ video display rotation ที่ไม่ใช่มุมฉาก")
        return "video", dict(
            width=first.height if rotation % 180 else first.width,
            height=first.width if rotation % 180 else first.height,
            duration_seconds=duration,
            codec=stream.codec_context.name,
            time_base=str(stream.time_base),
            start_pts=first.pts,
            start_seconds=float(first.pts * stream.time_base),
            rotation_degrees_counterclockwise=rotation,
            browser_playable=stream.codec_context.name in ("h264", "av1", "vp9"),
        )


def sample_frames(path, kind, interval):
    import numpy as np

    if kind == "image":
        with Image.open(path) as im:
            rgb = np.asarray(ImageOps.exif_transpose(im).convert("RGB"))
        yield 0, 0.0, None, None, rgb
        return
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        next_at = 0.0
        start = None
        previous = -1.0
        index = 0
        for frame in container.decode(stream):
            if frame.pts is None:
                raise ValueError("VIDEO_FRAME_WITHOUT_PTS")
            seconds = float(frame.pts * stream.time_base)
            if start is None:
                start = seconds
            t = seconds - start
            if t < previous - 1e-6:
                raise ValueError("NONMONOTONIC_VIDEO_PTS")
            previous = t
            if t > s.MAX_VIDEO_SECONDS:
                raise ValueError("MAX_VIDEO_DURATION_EXCEEDED")
            if t + 1e-7 < next_at:
                continue
            if index >= s.MAX_SAMPLED_FRAMES:
                raise ValueError("MAX_SAMPLED_FRAMES_EXCEEDED")
            # Decode streaming; frame PTS, not nominal FPS or upload time.
            rotation = int(frame.rotation)
            if rotation % 90:
                raise ValueError("UNSUPPORTED_DISPLAY_ROTATION")
            rgb = frame.to_ndarray(format="rgb24")
            if rotation:
                rgb = np.rot90(rgb, k=rotation // 90).copy()
            yield index, t, int(frame.pts), str(stream.time_base), rgb
            index += 1
            next_at = (int(t / interval) + 1) * interval
        if not index:
            raise ValueError("NO_DECODABLE_VIDEO_FRAME")
