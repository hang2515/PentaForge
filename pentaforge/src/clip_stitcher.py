"""Stitch multiple clips together with transitions."""

from __future__ import annotations

from . import _ffmpeg_init  # noqa: F401 — init bundled FFmpeg binary
import os
import tempfile
import ffmpeg

from .config_parser import ExportConfig, TransitionConfig


def _has_audio(path: str) -> bool:
    info = ffmpeg.probe(path)
    return any(s.get("codec_type") == "audio" for s in info.get("streams", []))


def _duration(path: str) -> float:
    return float(ffmpeg.probe(path)["format"]["duration"])


def _fps(path: str) -> float:
    """Detect frame rate of the first video stream."""
    info = ffmpeg.probe(path)
    for s in info.get("streams", []):
        if s.get("codec_type") == "video":
            # r_frame_rate is a string like "30/1" or "30000/1001"
            fps_str = s.get("r_frame_rate", "30/1")
            num, den = fps_str.split("/")
            return float(num) / float(den)
    return 30.0


def _generate_silent_audio(duration: float, output: str):
    """Generate a silent audio file of the given duration."""
    stream = ffmpeg.input(
        f"anullsrc=channel_layout=stereo:sample_rate=44100", f="lavfi"
    )
    stream = ffmpeg.output(stream, output, t=duration, acodec="aac").global_args("-y")
    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)


def _normalize_codec(codec: str) -> str:
    aliases = {
        "h264": "libx264",
        "x264": "libx264",
        "h265": "libx265",
        "hevc": "libx265",
        "x265": "libx265",
    }
    return aliases.get(codec.lower(), codec)


def _export_kwargs(export: ExportConfig) -> dict:
    kwargs = {
        "vcodec": _normalize_codec(export.codec),
        "preset": export.preset,
        "pix_fmt": "yuv420p",
        "acodec": "aac",
    }
    if export.bitrate:
        kwargs["video_bitrate"] = export.bitrate
    return kwargs


def _apply_export_filters(video, export: ExportConfig):
    if export.resolution:
        width, height = export.resolution.lower().split("x", 1)
        video = video.filter("scale", int(width), int(height))
    if export.fps:
        video = video.filter("fps", fps=export.fps)
    return video


def _concat_hard_cut(v_nodes: list, a_nodes: list, has_audio: bool):
    if has_audio:
        streams = []
        for video, audio in zip(v_nodes, a_nodes):
            streams.extend([video, audio])
        joined = ffmpeg.concat(*streams, v=1, a=1).node
        return joined[0], joined[1]
    return ffmpeg.concat(*v_nodes, v=1, a=0), None


def _concat_pair(out_v, out_a, next_v, next_a, has_audio: bool):
    if has_audio:
        joined = ffmpeg.concat(out_v, out_a, next_v, next_a, v=1, a=1).node
        return joined[0], joined[1]
    return ffmpeg.concat(out_v, next_v, v=1, a=0), None


def _do_stitch(
    clip_paths: list[str],
    audio_paths: list[str],
    output: str,
    transitions: list[TransitionConfig],
    overwrite: bool,
    has_audio: bool,
    export: ExportConfig,
):
    """Build and run the xfade+acrossfade filter graph."""
    inputs = [ffmpeg.input(p) for p in clip_paths]
    ad_inputs = [ffmpeg.input(p) for p in audio_paths] if has_audio else []

    v_nodes = []
    a_nodes = []

    # Detect resolution from first clip
    first_info = ffmpeg.probe(clip_paths[0])
    first_v = next(s for s in first_info.get("streams", []) if s.get("codec_type") == "video")
    base_w = first_v["width"]
    base_h = first_v["height"]

    for i, inp in enumerate(inputs):
        v = inp.video.filter("setpts", "PTS-STARTPTS")
        clip_fps = _fps(clip_paths[i])
        v = v.filter("fps", fps=clip_fps)
        v = v.filter("scale", base_w, base_h, force_original_aspect_ratio="decrease")
        v = v.filter("pad", base_w, base_h, "(ow-iw)/2", "(oh-ih)/2")
        v = v.filter("format", pix_fmts="yuv420p")
        v_nodes.append(v)
        if has_audio:
            a = ad_inputs[i].audio.filter("asetpts", "PTS-STARTPTS")
            a_nodes.append(a)

    if len(v_nodes) == 1:
        out_v = v_nodes[0]
        out_a = a_nodes[0] if has_audio else None
    elif all(t.duration <= 0 for t in transitions):
        out_v, out_a = _concat_hard_cut(v_nodes, a_nodes, has_audio)
    else:
        out_v = v_nodes[0]
        out_a = a_nodes[0] if has_audio else None
        current_duration = _duration(clip_paths[0])
        for i in range(1, len(v_nodes)):
            transition = transitions[i - 1]
            next_duration = _duration(clip_paths[i])
            if transition.duration <= 0:
                out_v, out_a = _concat_pair(
                    out_v,
                    out_a,
                    v_nodes[i],
                    a_nodes[i] if has_audio else None,
                    has_audio,
                )
                current_duration += next_duration
                continue

            offset = max(0, current_duration - transition.duration)
            out_v = ffmpeg.filter(
                [out_v, v_nodes[i]],
                "xfade",
                transition=transition.type,
                duration=transition.duration,
                offset=offset,
            )
            if has_audio:
                out_a = ffmpeg.filter(
                    [out_a, a_nodes[i]],
                    "acrossfade",
                    duration=transition.duration,
                )
            current_duration += next_duration - transition.duration

    out_v = _apply_export_filters(out_v, export)
    kwargs = _export_kwargs(export)

    if out_a is not None:
        stream = ffmpeg.output(
            out_v, out_a, output,
            **kwargs,
        )
    else:
        kwargs.pop("acodec", None)
        stream = ffmpeg.output(
            out_v, output,
            **kwargs,
        )
    if overwrite:
        stream = stream.global_args("-y")
    try:
        ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg stitch error:\n{e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}")


def stitch_clips(
    clip_paths: list[str],
    output: str,
    transition_type: str = "fade",
    transition_dur: float = 0.3,
    transitions: list[TransitionConfig] | None = None,
    export: ExportConfig | None = None,
    overwrite: bool = True,
) -> None:
    """Stitch multiple clips into a single video with transitions.

    Args:
        clip_paths: Ordered list of clip file paths to stitch.
        output: Output video file path.
        transition_type: xfade transition type (fade, fadeblack, fadewhite,
                        dissolve, wipeleft, wiperight, wipeup, wipedown, etc.)
        transition_dur: Duration of transition in seconds.
        transitions: Optional per-boundary transition configs. Length must be
                     len(clip_paths) - 1.
    """
    if not clip_paths:
        raise ValueError("No clips to stitch")
    export = export or ExportConfig()
    if transitions is None:
        transitions = [
            TransitionConfig(type=transition_type, duration=transition_dur)
            for _ in range(max(0, len(clip_paths) - 1))
        ]
    elif len(transitions) != len(clip_paths) - 1:
        raise ValueError("transitions length must be one less than clip_paths length")

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    has_audio_list = [_has_audio(p) for p in clip_paths]
    any_audio = any(has_audio_list)

    if len(clip_paths) == 1:
        inp = ffmpeg.input(clip_paths[0])
        video = _apply_export_filters(inp.video, export)
        kwargs = _export_kwargs(export)
        if any_audio:
            stream = ffmpeg.output(video, inp.audio, output, **kwargs)
        else:
            kwargs.pop("acodec", None)
            stream = ffmpeg.output(video, output, **kwargs)
        if overwrite:
            stream = stream.global_args("-y")
        try:
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
        except ffmpeg.Error as e:
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
            raise RuntimeError(f"FFmpeg stitch error:\n{stderr}")
        return

    # For multi-clip xfade, all clips need an audio track for acrossfade.
    # Fill missing audio with generated silent audio temp files.
    tmpdir = tempfile.mkdtemp(prefix="pfstitch_")
    audio_paths: list[str] = []
    try:
        for i, p in enumerate(clip_paths):
            if has_audio_list[i]:
                audio_paths.append(p)  # audio embedded in clip, same path
            elif any_audio:
                silent = os.path.join(tmpdir, f"silent_{i:04d}.m4a")
                _generate_silent_audio(_duration(p), silent)
                audio_paths.append(silent)
            else:
                audio_paths.append(p)

        _do_stitch(
            clip_paths=clip_paths,
            audio_paths=audio_paths,
            output=output,
            transitions=transitions,
            overwrite=overwrite,
            has_audio=any_audio,
            export=export,
        )
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
