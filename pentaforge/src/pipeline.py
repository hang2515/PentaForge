"""Pipeline orchestrator: ties all modules together."""

import os
import tempfile
import shutil
from dataclasses import dataclass

from .config_parser import PipelineConfig, ClipConfig
from .clip_extractor import extract_video
from .audio_processor import mix_audio_for_clip, mux_video_audio
from .clip_stitcher import stitch_clips


@dataclass
class PipelineResult:
    success: bool
    output_path: str
    errors: list[str]
    temp_dir: str


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

            # Step 1: Extract video segment
            video_temp = os.path.join(temp_dir, f"video_{i:04d}.mp4")
            keep_audio = not config.audio_enabled
            extract_video(config.source, clip.start, clip.duration, video_temp, keep_audio=keep_audio)

            # Step 2-3: Process audio only when enabled and BGM is configured
            if config.audio_enabled and bgm:
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
    total_steps = total_clips * 3 + 1
    step = 0

    try:
        for i, clip in enumerate(config.clips):
            bgm = clip.bgm if clip.bgm else config.bgm
            sfx_path = config.sfx.get(clip.kill_type, "") if clip.kill_type else ""

            step += 1
            callback(step, total_steps, f"Extracting clip {i+1}/{total_clips}: {clip.label or clip.kill_type}")

            video_temp = os.path.join(temp_dir, f"video_{i:04d}.mp4")
            keep_audio = not config.audio_enabled
            extract_video(config.source, clip.start, clip.duration, video_temp, keep_audio=keep_audio)

            if config.audio_enabled and bgm:
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
        )

    except Exception as e:
        errors.append(str(e))
        return PipelineResult(success=False, output_path="", errors=errors, temp_dir=temp_dir)

    return PipelineResult(success=True, output_path=config.output, errors=[], temp_dir=temp_dir)


def cleanup_temp(temp_dir: str) -> None:
    """Remove temporary working directory and all contents."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
