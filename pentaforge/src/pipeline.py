"""Pipeline orchestrator: ties all modules together."""

from __future__ import annotations

import logging
import os
import tempfile
import shutil
from dataclasses import dataclass

from .config_parser import PipelineConfig, ClipConfig, TransitionConfig

log = logging.getLogger("pentaforge.pipeline")
from .clip_extractor import extract_video
from .audio_processor import mix_audio_for_clip, mux_video_audio
from .clip_stitcher import stitch_clips


@dataclass
class PipelineResult:
    success: bool
    output_path: str
    errors: list[str]
    temp_dir: str


def _clip_transitions(config: PipelineConfig) -> list[TransitionConfig]:
    transitions: list[TransitionConfig] = []
    for clip in config.clips[:-1]:
        transitions.append(clip.transition_after or config.transitions)
    return transitions


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """Execute the full highlight clipping pipeline.

    Steps:
      1. For each clip: extract video segment (no audio)
      2. For each clip: create mixed audio (BGM + SFX)
      3. Mux video + audio for each clip
      4. Stitch all clips with transitions
      5. Clean up temp files
    """
    errors: list[str] = []

    # Resolve temp directory
    if config.temp_dir:
        temp_dir = config.temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    else:
        temp_dir = tempfile.mkdtemp(prefix="pentaforge_")

    clip_files: list[str] = []

    try:
        for i, clip in enumerate(config.clips):
            # Determine which BGM to use
            bgm = clip.bgm if clip.bgm else config.bgm

            # Determine SFX path
            sfx_path = config.sfx.get(clip.kill_type, "") if clip.kill_type else ""

            # Resolve source file for this clip (multi-source support)
            source_path = config.source_for(clip)

            # Step 1: Extract video segment
            video_temp = os.path.join(temp_dir, f"video_{i:04d}.mp4")
            has_audio_mix = config.audio_enabled and bool(bgm)
            keep_audio = not has_audio_mix
            extract_video(source_path, clip.start, clip.duration, video_temp, keep_audio=keep_audio)

            # Step 2-3: Process audio only when audio_enabled and BGM is configured
            if has_audio_mix:
                audio_temp = os.path.join(temp_dir, f"audio_{i:04d}.m4a")
                sfx_offset = clip.sfx_offset
                if sfx_offset is None:
                    sfx_offset = max(0, clip.duration - 1.0)

                mix_audio_for_clip(
                    bgm_path=bgm,
                    clip_duration=clip.duration,
                    output=audio_temp,
                    sfx_path=sfx_path,
                    sfx_offset=sfx_offset,
                    bgm_volume=config.bgm_volume,
                    sfx_volume=config.sfx_volume,
                )

                muxed = os.path.join(temp_dir, f"clip_{i:04d}.mp4")
                mux_video_audio(video_temp, audio_temp, muxed)
                clip_files.append(muxed)
            else:
                clip_files.append(video_temp)

        # Step 4: Stitch clips
        stitch_clips(
            clip_paths=clip_files,
            output=config.output,
            transition_type=config.transitions.type,
            transition_dur=config.transitions.duration,
            transitions=_clip_transitions(config),
            export=config.export,
        )

    except Exception as e:
        errors.append(str(e))
        return PipelineResult(
            success=False,
            output_path="",
            errors=errors,
            temp_dir=temp_dir,
        )

    return PipelineResult(
        success=True,
        output_path=config.output,
        errors=[],
        temp_dir=temp_dir,
    )


def run_pipeline_with_progress(config: PipelineConfig, callback) -> PipelineResult:
    """Same as run_pipeline but calls callback(step, total, message) at each stage."""
    errors: list[str] = []

    if config.temp_dir:
        temp_dir = config.temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    else:
        temp_dir = tempfile.mkdtemp(prefix="pentaforge_")

    clip_files: list[str] = []
    total_clips = len(config.clips)
    # Each clip: 1 extract step, plus 2 audio steps if audio is enabled with BGM
    total_steps = 1  # final stitch
    for clip in config.clips:
        bgm = clip.bgm if clip.bgm else config.bgm
        has_audio_mix = config.audio_enabled and bool(bgm)
        total_steps += 3 if has_audio_mix else 1
    step = 0

    try:
        # Log source video info for diagnostics
        from . import _ffmpeg_init  # noqa
        import ffmpeg as _ff
        for si, src in enumerate(config.sources):
            if src.path and os.path.exists(src.path):
                try:
                    probe = _ff.probe(src.path)
                    fmt = probe.get("format", {})
                    v_stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), {})
                    log.info(f"Source[{si}]: {src.path} | duration={fmt.get('duration', '?')}s | "
                             f"codec={v_stream.get('codec_name', '?')} | "
                             f"size={v_stream.get('width', '?')}x{v_stream.get('height', '?')} | "
                             f"pix_fmt={v_stream.get('pix_fmt', '?')} | fps={v_stream.get('r_frame_rate', '?')}")
                except Exception as e:
                    log.warning(f"Source[{si}] probe failed: {e}")
            else:
                log.warning(f"Source[{si}] not found: {src.path}")

        for i, clip in enumerate(config.clips):
            bgm = clip.bgm if clip.bgm else config.bgm
            sfx_path = config.sfx.get(clip.kill_type, "") if clip.kill_type else ""

            step += 1
            callback(step, total_steps, f"Extracting clip {i+1}/{total_clips}: {clip.label or clip.kill_type}")

            video_temp = os.path.join(temp_dir, f"video_{i:04d}.mp4")
            has_audio_mix = config.audio_enabled and bool(bgm)
            keep_audio = not has_audio_mix
            source_path = config.source_for(clip)
            log.info(f"Extract: source={source_path}, start={clip.start}, duration={clip.duration}, output={video_temp}, keep_audio={keep_audio}")
            callback(step, total_steps, f"Extracting: {os.path.basename(source_path)} [{clip.start:.1f}s - {clip.end:.1f}s]")
            extract_video(source_path, clip.start, clip.duration, video_temp, keep_audio=keep_audio)
            if os.path.exists(video_temp):
                size_kb = os.path.getsize(video_temp) / 1024
                log.info(f"Extracted clip {i+1}: {size_kb:.0f} KB")
                callback(step, total_steps, f"Extracted clip {i+1}: {size_kb:.0f} KB")

            if has_audio_mix:
                step += 1
                callback(step, total_steps, f"Mixing audio for clip {i+1}/{total_clips}")

                audio_temp = os.path.join(temp_dir, f"audio_{i:04d}.m4a")
                sfx_offset = clip.sfx_offset
                if sfx_offset is None:
                    sfx_offset = max(0, clip.duration - 1.0)

                mix_audio_for_clip(
                    bgm_path=bgm,
                    clip_duration=clip.duration,
                    output=audio_temp,
                    sfx_path=sfx_path,
                    sfx_offset=sfx_offset,
                    bgm_volume=config.bgm_volume,
                    sfx_volume=config.sfx_volume,
                )

                step += 1
                callback(step, total_steps, f"Muxing clip {i+1}/{total_clips}")

                muxed = os.path.join(temp_dir, f"clip_{i:04d}.mp4")
                mux_video_audio(video_temp, audio_temp, muxed)
                clip_files.append(muxed)
            else:
                clip_files.append(video_temp)

        step += 1
        callback(step, total_steps, f"Stitching {len(clip_files)} clips with transitions...")

        stitch_clips(
            clip_paths=clip_files,
            output=config.output,
            transition_type=config.transitions.type,
            transition_dur=config.transitions.duration,
            transitions=_clip_transitions(config),
            export=config.export,
        )

    except Exception as e:
        errors.append(str(e))
        return PipelineResult(success=False, output_path="", errors=errors, temp_dir=temp_dir)

    return PipelineResult(success=True, output_path=config.output, errors=[], temp_dir=temp_dir)


def cleanup_temp(temp_dir: str) -> None:
    """Remove temporary working directory and all contents."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
