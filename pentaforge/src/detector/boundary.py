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


def events_to_penta_clip_configs(
    events: Iterable[KillEvent],
    *,
    pre_double_roll: float = 15.0,
    post_penta_roll: float = 3.0,
    chain_gap: float = 12.0,
    merge_gap: float = 2.0,
    video_duration: float | None = None,
) -> list[ClipConfig]:
    """Convert multi-kill chains containing a penta kill into clip configs."""
    windows: list[ClipWindow] = []
    for chain in _event_chains(events, chain_gap=chain_gap):
        penta_events = [event for event in chain if event.kill_type == "penta_kill"]
        if not penta_events:
            continue

        start_event = next((event for event in chain if event.kill_type == "double_kill"), chain[0])
        penta_event = penta_events[-1]
        start = max(0.0, start_event.time - pre_double_roll)
        end = penta_event.time + post_penta_roll
        if video_duration is not None:
            end = min(float(video_duration), end)
        windows.append(ClipWindow(start=start, end=end, events=list(chain)))

    clips: list[ClipConfig] = []
    for index, window in enumerate(merge_clip_windows(windows, merge_gap=merge_gap), start=1):
        clips.append(
            ClipConfig(
                start=window.start,
                end=window.end,
                kill_type="penta_kill",
                label=f"Auto penta kill {index}",
            )
        )
    return clips


def _event_chains(events: Iterable[KillEvent], *, chain_gap: float) -> list[list[KillEvent]]:
    chains: list[list[KillEvent]] = []
    for event in sorted(events, key=lambda item: item.time):
        if not chains or event.time - chains[-1][-1].time > chain_gap:
            chains.append([event])
            continue
        chains[-1].append(event)
    return chains


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
