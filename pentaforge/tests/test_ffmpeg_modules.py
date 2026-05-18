"""Integration tests for the FFmpeg-based modules."""

import os
import tempfile
import pytest

from src import _ffmpeg_init  # noqa: F401 — init bundled FFmpeg binary
import ffmpeg

from src.clip_extractor import extract_video, get_video_duration
from src.audio_processor import mix_audio_for_clip, mux_video_audio
from src.clip_stitcher import stitch_clips
from src.config_parser import ExportConfig, TransitionConfig


def _ffmpeg_available():
    """Check if FFmpeg is available."""
    try:
        ffmpeg.run(ffmpeg.input("testsrc=duration=0.1", f="lavfi").output("-", f="null"), capture_stdout=True, capture_stderr=True)
        return True
    except Exception:
        return False


ffmpeg_skip = pytest.mark.skipif(
    not _ffmpeg_available(),
    reason="FFmpeg not available",
)


def _generate_test_video(path: str, duration: float = 3.0, label: str = "0"):
    """Generate a constant-frame-rate test video with a text label."""
    stream = ffmpeg.input(
        f"testsrc=duration={duration}:size=640x480:rate=30",
        f="lavfi",
    ).filter("drawtext", text=f"Clip {label}", fontsize=48, fontcolor="white",
             x="(w-text_w)/2", y="(h-text_h)/2")
    stream = ffmpeg.output(stream, path, r=30)
    stream = stream.global_args("-y")
    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)


def _generate_test_audio(path: str, duration: float = 3.0, freq: int = 440):
    """Generate a test audio file (sine wave)."""
    stream = ffmpeg.input(
        f"sine=frequency={freq}:duration={duration}",
        f="lavfi",
    )
    stream = ffmpeg.output(stream, path)
    stream = stream.global_args("-y")
    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)


def _has_audio(path: str) -> bool:
    info = ffmpeg.probe(path)
    return any(s.get("codec_type") == "audio" for s in info.get("streams", []))


def _video_stream(path: str) -> dict:
    info = ffmpeg.probe(path)
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream
    raise AssertionError("No video stream found")


@ffmpeg_skip
class TestClipExtractor:
    def test_extract_video(self):
        tmpdir = tempfile.mkdtemp(prefix="pftest_")
        try:
            source = os.path.join(tmpdir, "source.mp4")
            output = os.path.join(tmpdir, "extracted.mp4")
            _generate_test_video(source, duration=5.0, label="Source")

            extract_video(source, start=1.0, duration=2.0, output=output)
            assert os.path.exists(output)

            dur = get_video_duration(output)
            assert 1.5 <= dur <= 2.5
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_extract_video_can_keep_audio(self):
        tmpdir = tempfile.mkdtemp(prefix="pftest_")
        try:
            video = os.path.join(tmpdir, "video.mp4")
            audio = os.path.join(tmpdir, "audio.wav")
            source = os.path.join(tmpdir, "source.mp4")
            output = os.path.join(tmpdir, "extracted.mp4")
            _generate_test_video(video, duration=3.0, label="AV")
            _generate_test_audio(audio, duration=3.0, freq=440)
            mux_video_audio(video, audio, source)

            extract_video(source, start=0.5, duration=1.5, output=output, keep_audio=True)

            assert os.path.exists(output)
            assert _has_audio(output)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


@ffmpeg_skip
class TestAudioProcessor:
    def test_mix_bgm_only(self):
        tmpdir = tempfile.mkdtemp(prefix="pftest_")
        try:
            bgm = os.path.join(tmpdir, "bgm.wav")
            output = os.path.join(tmpdir, "mixed.m4a")
            _generate_test_audio(bgm, duration=5.0, freq=440)

            mix_audio_for_clip(
                bgm_path=bgm,
                clip_duration=3.0,
                output=output,
                bgm_volume=0.5,
            )
            assert os.path.exists(output)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_mix_bgm_with_sfx(self):
        tmpdir = tempfile.mkdtemp(prefix="pftest_")
        try:
            bgm = os.path.join(tmpdir, "bgm.wav")
            sfx = os.path.join(tmpdir, "sfx.wav")
            output = os.path.join(tmpdir, "mixed.m4a")
            _generate_test_audio(bgm, duration=5.0, freq=440)
            _generate_test_audio(sfx, duration=0.5, freq=880)

            mix_audio_for_clip(
                bgm_path=bgm,
                clip_duration=3.0,
                output=output,
                sfx_path=sfx,
                sfx_offset=1.0,
                bgm_volume=0.5,
                sfx_volume=0.8,
            )
            assert os.path.exists(output)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_mux_video_audio(self):
        tmpdir = tempfile.mkdtemp(prefix="pftest_")
        try:
            video = os.path.join(tmpdir, "video.mp4")
            audio = os.path.join(tmpdir, "audio.m4a")
            output = os.path.join(tmpdir, "muxed.mp4")

            _generate_test_video(video, duration=2.0, label="Mux")
            _generate_test_audio(audio, duration=2.0, freq=440)

            # Create video-only version first
            video_only = os.path.join(tmpdir, "video_only.mp4")
            extract_video(video, start=0, duration=2.0, output=video_only)

            mux_video_audio(video_only, audio, output)
            assert os.path.exists(output)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


@ffmpeg_skip
class TestClipStitcher:
    def test_stitch_two_clips(self):
        tmpdir = tempfile.mkdtemp(prefix="pftest_")
        try:
            clip1 = os.path.join(tmpdir, "clip1.mp4")
            clip2 = os.path.join(tmpdir, "clip2.mp4")
            output = os.path.join(tmpdir, "stitched.mp4")

            _generate_test_video(clip1, duration=2.0, label="One")
            _generate_test_video(clip2, duration=2.0, label="Two")

            stitch_clips(
                [clip1, clip2],
                output,
                transition_type="fade",
                transition_dur=0.3,
                export=ExportConfig(resolution="640x480", fps=30),
            )
            assert os.path.exists(output)

            dur = get_video_duration(output)
            # Expected: 2.0 + 2.0 - 0.3 = 3.7 (with transition)
            assert 3.0 <= dur <= 4.0
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_stitch_single_clip(self):
        tmpdir = tempfile.mkdtemp(prefix="pftest_")
        try:
            clip1 = os.path.join(tmpdir, "clip1.mp4")
            output = os.path.join(tmpdir, "stitched.mp4")

            _generate_test_video(clip1, duration=2.0, label="One")

            stitch_clips(
                [clip1],
                output,
                transition_type="fade",
                transition_dur=0.3,
                export=ExportConfig(resolution="640x480", fps=30),
            )
            assert os.path.exists(output)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_empty_clips_raises(self):
        with pytest.raises(ValueError):
            stitch_clips([], "output.mp4")

    def test_zero_transition_duration_hard_cuts(self):
        tmpdir = tempfile.mkdtemp(prefix="pftest_")
        try:
            clip1 = os.path.join(tmpdir, "clip1.mp4")
            clip2 = os.path.join(tmpdir, "clip2.mp4")
            output = os.path.join(tmpdir, "hard_cut.mp4")
            _generate_test_video(clip1, duration=1.0, label="A")
            _generate_test_video(clip2, duration=1.0, label="B")

            stitch_clips(
                [clip1, clip2],
                output,
                transition_dur=0,
                export=ExportConfig(resolution="640x480", fps=30),
            )

            assert os.path.exists(output)
            assert 1.8 <= get_video_duration(output) <= 2.2
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_per_clip_transitions(self):
        tmpdir = tempfile.mkdtemp(prefix="pftest_")
        try:
            clip1 = os.path.join(tmpdir, "clip1.mp4")
            clip2 = os.path.join(tmpdir, "clip2.mp4")
            clip3 = os.path.join(tmpdir, "clip3.mp4")
            output = os.path.join(tmpdir, "per_transition.mp4")
            _generate_test_video(clip1, duration=1.0, label="A")
            _generate_test_video(clip2, duration=1.0, label="B")
            _generate_test_video(clip3, duration=1.0, label="C")

            stitch_clips(
                [clip1, clip2, clip3],
                output,
                transitions=[
                    TransitionConfig(type="fade", duration=0.2),
                    TransitionConfig(type="wipeleft", duration=0.4),
                ],
                export=ExportConfig(resolution="640x480", fps=30),
            )

            assert os.path.exists(output)
            assert 2.2 <= get_video_duration(output) <= 2.6
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_transition_count_must_match_boundaries(self):
        with pytest.raises(ValueError, match="transitions length"):
            stitch_clips(
                ["a.mp4", "b.mp4", "c.mp4"],
                "output.mp4",
                transitions=[TransitionConfig(type="fade", duration=0.3)],
            )

    def test_export_config_controls_dimensions_and_fps(self):
        tmpdir = tempfile.mkdtemp(prefix="pftest_")
        try:
            clip1 = os.path.join(tmpdir, "clip1.mp4")
            output = os.path.join(tmpdir, "exported.mp4")
            _generate_test_video(clip1, duration=1.0, label="Export")

            stitch_clips(
                [clip1],
                output,
                export=ExportConfig(
                    resolution="320x240",
                    fps=24,
                    codec="h264",
                    bitrate="1M",
                    preset="veryfast",
                ),
            )

            stream = _video_stream(output)
            assert stream["width"] == 320
            assert stream["height"] == 240
            assert stream["r_frame_rate"] == "24/1"
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
