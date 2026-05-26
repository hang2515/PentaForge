"""Tests for Phase 2 clip boundary generation."""

from src.detector.boundary import events_to_clip_configs, events_to_clip_windows, events_to_penta_clip_configs
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


def test_events_to_penta_clip_configs_uses_double_to_penta_chain():
    clips = events_to_penta_clip_configs([
        KillEvent(time=130.0, kill_type="double_kill", text="双杀"),
        KillEvent(time=135.0, kill_type="triple_kill", text="三杀"),
        KillEvent(time=140.0, kill_type="quadra_kill", text="四杀"),
        KillEvent(time=144.0, kill_type="penta_kill", text="五杀"),
    ])

    assert len(clips) == 1
    assert clips[0].start == 115.0
    assert clips[0].end == 147.0
    assert clips[0].kill_type == "penta_kill"
    assert clips[0].label == "Auto penta kill 1"


def test_events_to_penta_clip_configs_falls_back_to_earliest_chain_event():
    clips = events_to_penta_clip_configs([
        KillEvent(time=40.0, kill_type="triple_kill", text="Triple Kill"),
        KillEvent(time=46.0, kill_type="penta_kill", text="Penta Kill"),
    ])

    assert len(clips) == 1
    assert clips[0].start == 25.0
    assert clips[0].end == 49.0


def test_events_to_penta_clip_configs_ignores_chains_without_penta():
    clips = events_to_penta_clip_configs([
        KillEvent(time=20.0, kill_type="double_kill", text="Double Kill"),
        KillEvent(time=24.0, kill_type="triple_kill", text="Triple Kill"),
    ])

    assert clips == []


def test_events_to_penta_clip_configs_respects_chain_gap_and_video_bounds():
    clips = events_to_penta_clip_configs([
        KillEvent(time=3.0, kill_type="double_kill", text="Double Kill"),
        KillEvent(time=20.0, kill_type="penta_kill", text="Penta Kill"),
        KillEvent(time=95.0, kill_type="double_kill", text="Double Kill"),
        KillEvent(time=99.0, kill_type="penta_kill", text="Penta Kill"),
    ], chain_gap=12, video_duration=100)

    assert len(clips) == 2
    assert clips[0].start == 5.0
    assert clips[0].end == 23.0
    assert clips[1].start == 80.0
    assert clips[1].end == 100.0


def test_events_to_penta_clip_configs_merges_nearby_penta_windows():
    clips = events_to_penta_clip_configs([
        KillEvent(time=100.0, kill_type="double_kill", text="Double Kill"),
        KillEvent(time=110.0, kill_type="penta_kill", text="Penta Kill"),
        KillEvent(time=115.0, kill_type="double_kill", text="Double Kill"),
        KillEvent(time=123.0, kill_type="penta_kill", text="Penta Kill"),
    ], chain_gap=12, merge_gap=5)

    assert len(clips) == 1
    assert clips[0].start == 85.0
    assert clips[0].end == 126.0
