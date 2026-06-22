import os
import subprocess


def _web_clip_path(source_path: str) -> str:
    base, ext = os.path.splitext(source_path)
    return f"{base}_web{ext or '.mp4'}"


def _is_h264(path: str) -> bool:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        return result.stdout.strip().lower() in {"h264", "avc1"}
    except Exception:
        return False


def normalize_media_path(path: str | None, media_root: str) -> str:
    if not path:
        return ""
    cleaned = path.strip()
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    cleaned = cleaned.lstrip("/")
    if cleaned.startswith("media/"):
        cleaned = cleaned[len("media/") :]
    return os.path.join(media_root, cleaned)


def ensure_web_playable_clip(source_path: str) -> str:
    """Return a browser-compatible H.264 MP4 path, transcoding if needed."""
    if not source_path or not os.path.exists(source_path):
        return ""

    if _is_h264(source_path):
        return source_path

    web_path = _web_clip_path(source_path)
    if os.path.exists(web_path) and os.path.getsize(web_path) > 0:
        return web_path

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                source_path,
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-an",
                web_path,
            ],
            check=True,
            capture_output=True,
            timeout=180,
        )
        if os.path.exists(web_path) and os.path.getsize(web_path) > 0:
            return web_path
    except Exception as exc:
        print(f"ffmpeg transcode failed for {source_path}: {exc}")

    return source_path
