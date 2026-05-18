"""Tests for Phase 2 clip boundary generation."""

from src.detector.boundary import events_to_clip_configs, events_to_clip_windows
from src.detector.event_parser import KillEvent


def test_events_to_clip_windows_adds_pre_and_post_roll():
    windows = events_to_clip_windows([
        KillEvent(time=20.0, kill_type="triple_kill", text="Triple Kill"),
    ], pre_roll=8, post_roll=4)

    assert len(windows) == 1
    assert windows[0].start == 12.0
    assert windows[0].end == 24.0


def test_events_to_clip_windows_clamps_to_video_bounds():
    windows = events_to_clip_windows([
        KillEvent(time=3.0, kill_type="double_kill", text="Double Kill"),
        KillEvent(time=98.0, kill_type="penta_kill", text="Penta Kill"),
    ], pre_roll=8, post_roll=5, merge_gap=0, video_duration=100)

    assert windows[0].start == 0.0
    assert windows[-1].end == 100.0


def test_events_to_clip_windows_merges_nearby_events():
    windows = events_to_clip_windows([
        KillEvent(time=20.0, kill_type="double_kill", text="Double Kill"),
        KillEvent(time=25.0, kill_type="triple_kill", text="Triple Kill"),
    ], pre_roll=4, post_roll=4, merge_gap=1)

    assert len(windows) == 1
    assert windows[0].start == 16.0
    assert windows[0].end == 29.0
    assert windows[0].primary_event.kill_type == "triple_kill"


def test_events_to_clip_configs_uses_primary_event():
    clips = events_to_clip_configs([
        KillEvent(time=20.0, kill_type="double_kill", text="Double Kill"),
        KillEvent(time=21.0, kill_type="penta_kill", text="Penta Kill"),
    ], pre_roll=2, post_roll=2)

    assert len(clips) == 1
    assert clips[0].kill_type == "penta_kill"
    assert clips[0].label == "Auto penta kill 1"
