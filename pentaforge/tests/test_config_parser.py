"""Tests for config_parser module."""

import os
import tempfile
import pytest

from src.config_parser import (
    parse_time,
    load_config,
    PipelineConfig,
    ClipConfig,
    TransitionConfig,
    ExportConfig,
)


class TestParseTime:
    def test_raw_seconds_int(self):
        assert parse_time(42) == 42.0

    def test_raw_seconds_float(self):
        assert parse_time(3.5) == 3.5

    def test_raw_seconds_string(self):
        assert parse_time("10.5") == 10.5

    def test_mm_ss(self):
        assert parse_time("1:30") == 90.0

    def test_mm_ss_with_milliseconds(self):
        assert parse_time("1:30.5") == 90.5

    def test_hh_mm_ss(self):
        assert parse_time("1:02:30") == 3750.0

    def test_hh_mm_ss_with_milliseconds(self):
        assert parse_time("1:02:30.500") == 3750.5

    def test_zero(self):
        assert parse_time("0:00") == 0.0

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_time("abc")


class TestLoadConfig:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp(prefix="pfcfg_")
        self.source = os.path.join(self.tmpdir, "test_source.mp4")
        # Create a minimal valid mp4 for file validation
        open(self.source, "wb").close()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def make_config(self, **overrides) -> str:
        base = {
            "source": self.source,
            "clips": [
                {"start": "0:10", "end": "0:20", "kill_type": "triple_kill"},
                {"start": "1:00", "end": "1:15", "kill_type": "penta_kill"},
            ],
        }
        base.update(overrides)
        import yaml
        return yaml.dump(base)

    def write_temp(self, content: str) -> str:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        )
        tmp.write(content)
        tmp.close()
        return tmp.name

    def test_basic_config(self):
        cfg_yaml = self.make_config()
        path = self.write_temp(cfg_yaml)
        try:
            config = load_config(path)
            assert config.source == self.source
            assert len(config.clips) == 2
            assert config.clips[0].start == 10.0
            assert config.clips[0].end == 20.0
            assert config.clips[0].kill_type == "triple_kill"
            assert config.clips[1].start == 60.0
            assert config.clips[1].end == 75.0
            assert config.clips[1].kill_type == "penta_kill"
        finally:
            os.unlink(path)

    def test_default_values(self):
        cfg_yaml = self.make_config()
        path = self.write_temp(cfg_yaml)
        try:
            config = load_config(path)
            assert config.output == "highlight_output.mp4"
            assert config.bgm_volume == 0.3
            assert config.sfx_volume == 0.8
            assert config.transitions.type == "fade"
            assert config.transitions.duration == 0.3
            assert config.export.resolution == "1920x1080"
            assert config.export.fps == 60
        finally:
            os.unlink(path)

    def test_custom_values(self):
        cfg_yaml = self.make_config(
            output="custom.mp4",
            bgm_volume=0.5,
            sfx_volume=0.9,
            transitions={"type": "dissolve", "duration": 0.5},
            export={"resolution": "1280x720", "fps": 30, "codec": "libx265", "bitrate": "8M"},
        )
        path = self.write_temp(cfg_yaml)
        try:
            config = load_config(path)
            assert config.output == "custom.mp4"
            assert config.bgm_volume == 0.5
            assert config.transitions.type == "dissolve"
            assert config.transitions.duration == 0.5
            assert config.export.resolution == "1280x720"
            assert config.export.fps == 30
            assert config.export.codec == "libx265"
        finally:
            os.unlink(path)

    def test_clip_label(self):
        cfg_yaml = self.make_config(
            clips=[{"start": "0:00", "end": "0:10", "label": "my highlight"}]
        )
        path = self.write_temp(cfg_yaml)
        try:
            config = load_config(path)
            assert config.clips[0].label == "my highlight"
        finally:
            os.unlink(path)

    def test_missing_source(self):
        cfg_yaml = self.make_config()
        del cfg_yaml  # noqa
        path = self.write_temp("clips: []")
        try:
            with pytest.raises(ValueError, match="source"):
                load_config(path)
        finally:
            os.unlink(path)

    def test_clip_start_after_end(self):
        cfg_yaml = self.make_config(
            clips=[{"start": "0:20", "end": "0:10"}]
        )
        path = self.write_temp(cfg_yaml)
        try:
            with pytest.raises(ValueError, match="start"):
                load_config(path)
        finally:
            os.unlink(path)

    def test_empty_config(self):
        path = self.write_temp("")
        try:
            with pytest.raises(ValueError):
                load_config(path)
        finally:
            os.unlink(path)

    def test_clip_duration_property(self):
        clip = ClipConfig(start=5.0, end=15.0)
        assert clip.duration == 10.0
