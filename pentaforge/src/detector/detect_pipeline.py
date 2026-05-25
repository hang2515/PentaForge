"""End-to-end detection pipeline from video frames to editable clips."""

from __future__ import annotations

from dataclasses import dataclass
import os
import tempfile
import shutil

from ..clip_extractor import get_video_duration
from ..config_parser import ClipConfig
from .boundary import events_to_clip_configs
from .event_parser import KillEvent, TextObservation, parse_kill_events
from .frame_sampler import Roi, extract_frame, frame_sample_times
from .ocr_reader import OcrReader


@dataclass
class DetectionResult:
    observations: list[TextObservation]
    events: list[KillEvent]
    clips: list[ClipConfig]


DEFAULT_KILL_BANNER_ROI = Roi(x=0.2, y=0.06, width=0.6, height=0.24)


def detect_candidates_from_video(
    source: str,
    *,
    reader: OcrReader | None = None,
    roi: Roi | None = DEFAULT_KILL_BANNER_ROI,
    interval: float = 0.5,
    pre_roll: float = 8.0,
    post_roll: float = 4.0,
    merge_gap: float = 2.0,
    min_confidence: float = 0.0,
    dedupe_window: float = 1.5,
    max_frames: int | None = None,
    temp_dir: str | None = None,
) -> DetectionResult:
    """Sample video frames, OCR them, and convert hits into clip candidates."""
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source video not found: {source}")
    if interval <= 0:
        raise ValueError("interval must be positive")

    if reader is None:
        from .paddleocr_reader import PaddleOcrReader

        reader = PaddleOcrReader(confidence_floor=min_confidence)

    duration = get_video_duration(source)
    sample_times = frame_sample_times(duration, interval)
    if max_frames is not None:
        sample_times = sample_times[:max(0, int(max_frames))]

    owns_temp_dir = temp_dir is None
    work_dir = temp_dir or tempfile.mkdtemp(prefix="pfocr_")
    os.makedirs(work_dir, exist_ok=True)

    observations: list[TextObservation] = []
    try:
        for index, timestamp in enumerate(sample_times):
            frame_path = os.path.join(work_dir, f"frame_{index:06d}.jpg")
            extract_frame(source, timestamp, frame_path, roi=roi)
            observations.extend(reader.read_frame(frame_path, timestamp=timestamp))
    finally:
        if owns_temp_dir:
            shutil.rmtree(work_dir, ignore_errors=True)

    events = parse_kill_events(
        observations,
        min_confidence=min_confidence,
        dedupe_window=dedupe_window,
    )
    clips = events_to_clip_configs(
        events,
        pre_roll=pre_roll,
        post_roll=post_roll,
        merge_gap=merge_gap,
        video_duration=duration,
    )
    return DetectionResult(observations=observations, events=events, clips=clips)
