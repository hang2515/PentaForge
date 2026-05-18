"""Initialize FFmpeg binary path using the bundled imageio-ffmpeg binary."""

import json
import re
import subprocess

import imageio_ffmpeg
import ffmpeg

_BINARY = imageio_ffmpeg.get_ffmpeg_exe()

_original_run = ffmpeg.run
_original_probe = ffmpeg.probe


def _patched_run(stream_spec, cmd=None, **kwargs):
    if cmd is None:
        cmd = _BINARY
    return _original_run(stream_spec, cmd=cmd, **kwargs)


def _patched_probe(filename, cmd=None, **kwargs):
    """Probe a media file using ffprobe or fallback to ffmpeg."""
    if cmd is None:
        cmd = _ffprobe_path()
    try:
        return _original_probe(filename, cmd=cmd, **kwargs)
    except (ffmpeg.Error, FileNotFoundError):
        return _probe_fallback(filename)


def _ffprobe_path():
    """Try to find ffprobe alongside ffmpeg binary."""
    import os
    ffmpeg_dir = os.path.dirname(_BINARY)
    ffprobe_exe = os.path.join(ffmpeg_dir, "ffprobe-win-x86_64-v7.1.exe")
    if os.path.exists(ffprobe_exe):
        return ffprobe_exe
    ffprobe_exe = os.path.join(ffmpeg_dir, "ffprobe.exe")
    if os.path.exists(ffprobe_exe):
        return ffprobe_exe
    # Not found — probe_fallback will be used via the except handler
    return "ffprobe"


_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)")
_VIDEO_RE = re.compile(r"Video:.*?,\s*(\d+)x(\d+).*?(\d+(?:\.\d+)?)\s*fps")


def _probe_fallback(filename):
    """Get media info using ffmpeg -i (when ffprobe is unavailable)."""
    result = subprocess.run(
        [_BINARY, "-i", filename],
        capture_output=True,
        text=True,
    )
    stderr = result.stderr or ""

    duration = 0.0
    m = _DURATION_RE.search(stderr)
    if m:
        duration = int(m.group(1)) * 3600.0 + int(m.group(2)) * 60.0 + float(m.group(3))

    has_video = "Video:" in stderr
    has_audio = "Audio:" in stderr
    video_stream = {"codec_type": "video"}
    m = _VIDEO_RE.search(stderr)
    if m:
        fps = float(m.group(3))
        video_stream.update({
            "width": int(m.group(1)),
            "height": int(m.group(2)),
            "r_frame_rate": f"{int(fps)}/1" if fps.is_integer() else f"{fps}/1",
        })

    return {
        "format": {"duration": duration},
        "streams": [
            *( [video_stream] if has_video else []),
            *( [{"codec_type": "audio"}] if has_audio else []),
        ],
    }


ffmpeg.run = _patched_run
ffmpeg.probe = _patched_probe
