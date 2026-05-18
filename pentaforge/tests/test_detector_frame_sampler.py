"""Tests for Phase 2 frame sampling helpers."""

import pytest

from src.detector.frame_sampler import Roi, frame_sample_times


def test_frame_sample_times():
    assert frame_sample_times(2.1, interval=0.5) == [0.0, 0.5, 1.0, 1.5, 2.0]


def test_frame_sample_times_rejects_invalid_interval():
    with pytest.raises(ValueError, match="interval"):
        frame_sample_times(10, interval=0)


def test_roi_to_pixels():
    roi = Roi(x=0.5, y=0.1, width=0.25, height=0.2)

    assert roi.to_pixels(1920, 1080) == (960, 108, 480, 216)


def test_roi_to_pixels_rejects_empty_size():
    with pytest.raises(ValueError, match="positive"):
        Roi(x=0, y=0, width=0, height=0.1).to_pixels(1920, 1080)
