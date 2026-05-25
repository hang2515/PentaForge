"""Turn detected kill events into highlight clip boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ..config_parser import ClipConfig
from .event_parser import KillEvent


@dataclass
class ClipWindow:
    """A merged highlight window derived from one or more kill events."""

    start: float
    end: float
    events: list[KillEvent] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def primary_event(self) -> KillEvent | None:
        if not self.events:
            return None
        return max(self.events, key=lambda event: _kill_rank(event.kill_type))


def events_to_clip_windows(
    events: Iterable[KillEvent],
    *,
    pre_roll: float = 8.0,
    post_roll: float = 4.0,
    merge_gap: float = 2.0,
    video_duration: float | None = None,
) -> list[ClipWindow]:
    """Create clip windows around events and merge nearby overlaps."""
    windows: list[ClipWindow] = []
    for event in sorted(events, key=lambda item: item.time):
        start = max(0.0, event.time - pre_roll)
        end = event.time + post_roll
        if video_duration is not None:
            end = min(float(video_duration), end)
        windows.append(ClipWindow(start=start, end=end, events=[event]))
    return merge_clip_windows(windows, merge_gap=merge_gap)


def merge_clip_windows(windows: Iterable[ClipWindow], *, merge_gap: float = 2.0) -> list[ClipWindow]:
    """Merge overlapping or nearly adjacent windows."""
    merged: list[ClipWindow] = []
    for window in sorted(windows, key=lambda item: item.start):
        if not merged or window.start > merged[-1].end + merge_gap:
            merged.append(window)
            continue
        merged[-1].end = max(merged[-1].end, window.end)
        merged[-1].events.extend(window.events)
    return merged


def events_to_clip_configs(
    events: Iterable[KillEvent],
    *,
    pre_roll: float = 8.0,
    post_roll: float = 4.0,
    merge_gap: float = 2.0,
    video_duration: float | None = None,
) -> list[ClipConfig]:
    """Convert detected events into Phase 1 ``ClipConfig`` objects."""
    clips: list[ClipConfig] = []
    for index, window in enumerate(
        events_to_clip_windows(
            events,
            pre_roll=pre_roll,
            post_roll=post_roll,
            merge_gap=merge_gap,
            video_duration=video_duration,
        ),
        start=1,
    ):
        primary = window.primary_event
        clips.append(
            ClipConfig(
                start=window.start,
                end=window.end,
                kill_type=primary.kill_type if primary else "",
                label=_label_for_window(index, window),
            )
        )
    return clips


def _kill_rank(kill_type: str) -> int:
    return {
        "double_kill": 2,
        "triple_kill": 3,
        "quadra_kill": 4,
        "penta_kill": 5,
    }.get(kill_type, 0)


def _label_for_window(index: int, window: ClipWindow) -> str:
    primary = window.primary_event
    if not primary:
        return f"Auto clip {index}"
    return f"Auto {primary.kill_type.replace('_', ' ')} {index}"
