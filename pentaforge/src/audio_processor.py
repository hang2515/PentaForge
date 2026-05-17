"""Audio processing: strip original audio, mix BGM and SFX."""

from . import _ffmpeg_init  # noqa: F401 — init bundled FFmpeg binary
import os
import ffmpeg


def mix_audio_for_clip(
    bgm_path: str,
    clip_duration: float,
    output: str,
    sfx_path: str = "",
    sfx_offset: float = 0.0,
    bgm_volume: float = 1.0,
    sfx_volume: float = 1.0,
    overwrite: bool = True,
) -> None:
    """Create a mixed audio track for a single highlight clip.

    Args:
        bgm_path: Path to background music file.
        clip_duration: Duration of the clip in seconds.
        output: Output audio file path.
        sfx_path: Path to kill sound effect file (optional).
        sfx_offset: Time offset (seconds from clip start) where SFX plays.
        bgm_volume: Volume multiplier for BGM (0.0 - 1.0).
        sfx_volume: Volume multiplier for SFX (0.0 - 1.0).
    """
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    bgm = ffmpeg.input(bgm_path)
    bgm = bgm.filter("atrim", duration=clip_duration)
    bgm = bgm.filter("volume", bgm_volume)
    bgm = bgm.filter("afade", t="out", st=max(0, clip_duration - 0.5), d=0.5)

    if sfx_path and os.path.exists(sfx_path):
        sfx = ffmpeg.input(sfx_path)
        sfx_offset_ms = max(0, int(sfx_offset * 1000))
        sfx = sfx.filter("adelay", f"{sfx_offset_ms}|{sfx_offset_ms}")
        sfx = sfx.filter("volume", sfx_volume)

        mixed = ffmpeg.filter([bgm, sfx], "amix", inputs=2, duration="first")
        mixed = mixed.filter("loudnorm", i=-16, tp=-1.5, lra=11)
    else:
        mixed = bgm.filter("loudnorm", i=-16, tp=-1.5, lra=11)

    stream = ffmpeg.output(mixed, output, acodec="aac", audio_bitrate="192k")
    if overwrite:
        stream = stream.global_args("-y")
    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)


def mux_video_audio(
    video_path: str,
    audio_path: str,
    output: str,
    overwrite: bool = True,
) -> None:
    """Mux a video-only file with an audio track into a single file."""
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    video = ffmpeg.input(video_path)
    audio = ffmpeg.input(audio_path)

    stream = ffmpeg.output(
        video.video,
        audio.audio,
        output,
        vcodec="copy",
        acodec="copy",
        shortest=None,
    )
    if overwrite:
        stream = stream.global_args("-y")
    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
