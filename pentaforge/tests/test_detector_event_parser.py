"""Tests for Phase 2 kill event parsing."""

from src.detector.event_parser import TextObservation, detect_kill_type, parse_kill_events


def test_detect_kill_type_english_and_chinese():
    assert detect_kill_type("Double Kill") == "double_kill"
    assert detect_kill_type("TRIPLE KILL!") == "triple_kill"
    assert detect_kill_type("quadra kill") == "quadra_kill"
    assert detect_kill_type("Pentakill") == "penta_kill"
    assert detect_kill_type("Penta Kill") == "penta_kill"
    assert detect_kill_type("双杀") == "double_kill"
    assert detect_kill_type("三杀") == "triple_kill"
    assert detect_kill_type("四杀") == "quadra_kill"
    assert detect_kill_type("五杀") == "penta_kill"
    assert detect_kill_type("双 杀") == "double_kill"
    assert detect_kill_type("雙殺") == "double_kill"
    assert detect_kill_type("五殺") == "penta_kill"


def test_parse_kill_events_filters_noise():
    events = parse_kill_events([
        TextObservation(time=10.0, text="minion slain", confidence=0.9),
        TextObservation(time=12.0, text="Double Kill", confidence=0.9),
    ])

    assert len(events) == 1
    assert events[0].time == 12.0
    assert events[0].kill_type == "double_kill"


def test_parse_kill_events_deduplicates_repeated_frames():
    events = parse_kill_events([
        TextObservation(time=20.0, text="Triple Kill", confidence=0.5),
        TextObservation(time=20.5, text="Triple Kill", confidence=0.8),
        TextObservation(time=24.0, text="Triple Kill", confidence=0.7),
    ])

    assert len(events) == 2
    assert events[0].time == 20.5
    assert events[0].confidence == 0.8
    assert events[1].time == 24.0


def test_parse_kill_events_honors_min_confidence():
    events = parse_kill_events([
        TextObservation(time=5.0, text="Penta Kill", confidence=0.4),
        TextObservation(time=8.0, text="Penta Kill", confidence=0.95),
    ], min_confidence=0.8)

    assert len(events) == 1
    assert events[0].time == 8.0
