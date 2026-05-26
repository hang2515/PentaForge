"""Phase 2 detection helpers for turning kill signals into clip windows."""

from .boundary import ClipWindow, events_to_clip_windows, events_to_clip_configs, events_to_penta_clip_configs
from .detect_pipeline import DetectionResult, detect_candidates_from_video
from .event_parser import KillEvent, TextObservation, parse_kill_events
from .frame_sampler import Roi, frame_sample_times

__all__ = [
    "ClipWindow",
    "DetectionResult",
    "KillEvent",
    "Roi",
    "TextObservation",
    "events_to_clip_configs",
    "events_to_penta_clip_configs",
    "events_to_clip_windows",
    "detect_candidates_from_video",
    "frame_sample_times",
    "parse_kill_events",
]
