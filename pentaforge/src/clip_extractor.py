"""Extract video segments from source footage using FFmpeg."""

from . import _ffmpeg_init  # noqa: F401 — init bundled FFmpeg binary
import os
import ffmpeg


def extract_video(
    source: str,
    start: float,
    duration: float,
    output: str,
    overwrite: bool = True,
    keep_audio: bool = False,
) -> None:
    """Extract a video segment from source.

    Uses stream copy when possible (no re-encode), re-encodes only when seeking
    to non-keyframe boundaries for accuracy. By default strips audio; pass
    keep_audio=True to preserve the original audio track.
    """
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    inp = ffmpeg.input(source, ss=start, t=duration)
    out_kwargs = {"vcodec": "libx264", "crf": 18, "preset": "veryfast", "pix_fmt": "yuv420p", "profile": "main"}
    if keep_audio:
        out_kwargs["acodec"] = "aac"
        stream = ffmpeg.output(inp.video, inp.audio, output, **out_kwargs)
    else:
        stream = ffmpeg.output(inp.video, output, an=None, **out_kwargs)
    if overwrite:
        stream = stream.global_args("-y")
    try:
        ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
        raise RuntimeError(f"FFmpeg extract error:\n{stderr}")


def extract_video_fast(
    source: str,
    start: float,
    duration: float,
    output: str,
    overwrite: bool = True,
) -> None:
    """Extract a video segment using stream copy (fast, but less precise).

    Stream copy is fast but may have slight timestamp inaccuracies at cut points
    (only accurate to nearest keyframe). Use when speed matters more than frame
    precision.
    """
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    stream = ffmpeg.input(source, ss=start, t=duration)
    stream = ffmpeg.output(
        stream.video,
        output,
        vcodec="copy",
        an=None,
    )
    if overwrite:
        stream = stream.global_args("-y")
    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)


def get_video_duration(path: str) -> float:
    """Get the duration of a video file in seconds."""
    probe = ffmpeg.probe(path)
    return float(probe["format"]["duration"])
