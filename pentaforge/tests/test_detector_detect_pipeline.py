"""Tests for the detector video-to-candidate pipeline."""

from src.detector import detect_pipeline
from src.detector.event_parser import TextObservation
from src.detector.frame_sampler import Roi


class FakeReader:
    def read_frame(self, image_path: str, *, timestamp: float):
        if timestamp == 1.0:
            return [TextObservation(time=timestamp, text="Triple Kill", confidence=0.9)]
        return []


def test_detect_candidates_from_video_with_fake_reader(monkeypatch, tmp_path):
    source = tmp_path / "source.mp4"
    source.write_bytes(b"fake")
    extracted = []

    monkeypatch.setattr(detect_pipeline, "get_video_duration", lambda _source: 2.0)

    def fake_extract_frame(_source, timestamp, output, roi=None):
        extracted.append((timestamp, output, roi))

    monkeypatch.setattr(detect_pipeline, "extract_frame", fake_extract_frame)

    result = detect_pipeline.detect_candidates_from_video(
        str(source),
        reader=FakeReader(),
        roi=Roi(x=0.2, y=0.1, width=0.5, height=0.2),
        interval=1.0,
        pre_roll=0.5,
        post_roll=0.5,
        max_frames=2,
    )

    assert [item[0] for item in extracted] == [0.0, 1.0]
    assert len(result.observations) == 1
    assert len(result.events) == 1
    assert result.events[0].kill_type == "triple_kill"
    assert len(result.clips) == 1
    assert result.clips[0].start == 0.5
    assert result.clips[0].end == 1.5


def test_detect_candidates_rejects_missing_video():
    try:
        detect_pipeline.detect_candidates_from_video("missing.mp4", reader=FakeReader())
    except FileNotFoundError as exc:
        assert "Source video" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")
