"""Parse and validate highlight configuration files."""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Optional, Union

import yaml


@dataclass
class TransitionConfig:
    type: str = "fade"
    duration: float = 0.3


@dataclass
class ClipConfig:
    start: float
    end: float
    kill_type: str = ""
    label: str = ""
    sfx_offset: Optional[float] = None
    bgm: Optional[str] = None
    transition_after: Optional[TransitionConfig] = None

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class ExportConfig:
    resolution: str = "1920x1080"
    fps: int = 60
    codec: str = "libx264"
    bitrate: str = "12M"
    preset: str = "medium"


@dataclass
class PipelineConfig:
    source: str
    output: str
    clips: list[ClipConfig]
    bgm: str = ""
    bgm_volume: float = 0.3
    sfx: dict[str, str] = field(default_factory=dict)
    sfx_volume: float = 0.8
    audio_enabled: bool = False
    transitions: TransitionConfig = field(default_factory=TransitionConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    temp_dir: str = ""


_TIME_COLON = re.compile(r"^(\d+):(\d+):(\d+(?:\.\d+)?)$")


def parse_time(raw: Union[str, int, float]) -> float:
    """Parse time string (HH:MM:SS.ms or MM:SS.ms or raw seconds) to float seconds."""
    if isinstance(raw, (int, float)):
        return float(raw)
    raw = str(raw).strip()
    m = _TIME_COLON.match(raw)
    if m:
        h = int(m.group(1))
        minute = int(m.group(2))
        sec = float(m.group(3))
        return h * 3600.0 + minute * 60.0 + sec
    m = re.match(r"^(\d+):(\d+(?:\.\d+)?)$", raw)
    if m:
        return int(m.group(1)) * 60.0 + float(m.group(2))
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"Invalid time format: {raw!r}")


def _validate_file(path: str, label: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{label} not found: {path}")


def _resolve_path(base_dir: str, path: str) -> str:
    if not path:
        return path
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(base_dir, path))


def _parse_bool(raw: Any, default: bool = False) -> bool:
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    value = str(raw).strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {raw!r}")


def _load_raw_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        if path.lower().endswith(".json"):
            raw = json.load(f)
        else:
            raw = yaml.safe_load(f)
    if raw is None:
        raise ValueError("Config file is empty")
    if not isinstance(raw, dict):
        raise ValueError("Config file must contain an object")
    return raw


def _parse_transition(raw: Any, default: TransitionConfig | None = None) -> TransitionConfig:
    default = default or TransitionConfig()
    if raw is None:
        return TransitionConfig(type=default.type, duration=default.duration)
    if not isinstance(raw, dict):
        raise ValueError("Transition config must be an object")
    return TransitionConfig(
        type=str(raw.get("type", default.type)),
        duration=float(raw.get("duration", default.duration)),
    )


def load_config(path: str) -> PipelineConfig:
    """Load and validate a YAML or JSON configuration file."""
    config_path = os.path.abspath(path)
    base_dir = os.path.dirname(config_path)
    raw = _load_raw_config(config_path)

    source = raw.get("source", "")
    if not source:
        raise ValueError("Missing required field: source")

    clips_raw = raw.get("clips", [])
    if not clips_raw:
        raise ValueError("No clips defined in config")

    transitions_raw = raw.get("transitions", {})
    transitions = _parse_transition(transitions_raw)

    clips = []
    for i, c in enumerate(clips_raw):
        try:
            start = parse_time(c["start"])
            end = parse_time(c["end"])
        except KeyError as e:
            raise ValueError(f"Clip {i}: missing required field {e}")
        if start >= end:
            raise ValueError(f"Clip {i}: start ({start}) >= end ({end})")

        sfx_offset = c.get("sfx_offset")
        if sfx_offset is not None:
            sfx_offset = float(sfx_offset)

        transition_after = None
        if "transition_after" in c:
            transition_after = _parse_transition(c.get("transition_after"), transitions)

        clips.append(ClipConfig(
            start=start,
            end=end,
            kill_type=str(c.get("kill_type", "")),
            label=str(c.get("label", "")),
            sfx_offset=sfx_offset,
            bgm=_resolve_path(base_dir, c.get("bgm", "")) or None,
            transition_after=transition_after,
        ))

    export_raw = raw.get("export", {})
    export = ExportConfig(
        resolution=export_raw.get("resolution", "1920x1080"),
        fps=int(export_raw.get("fps", 60)),
        codec=export_raw.get("codec", "libx264"),
        bitrate=export_raw.get("bitrate", "12M"),
        preset=export_raw.get("preset", "medium"),
    )

    sfx = {
        str(key): _resolve_path(base_dir, value)
        for key, value in raw.get("sfx", {}).items()
        if value
    }

    config = PipelineConfig(
        source=_resolve_path(base_dir, source),
        output=_resolve_path(base_dir, raw.get("output", "highlight_output.mp4")),
        clips=clips,
        bgm=_resolve_path(base_dir, raw.get("bgm", "")),
        bgm_volume=float(raw.get("bgm_volume", 0.3)),
        sfx=sfx,
        sfx_volume=float(raw.get("sfx_volume", 0.8)),
        audio_enabled=_parse_bool(raw.get("audio_enabled"), False),
        transitions=transitions,
        export=export,
        temp_dir=_resolve_path(base_dir, raw.get("temp_dir", "")),
    )

    # Validate files exist
    _validate_file(config.source, "Source video")
    if config.audio_enabled and not config.bgm:
        raise ValueError("audio_enabled is true, but no BGM file is configured")
    if config.audio_enabled and config.bgm:
        _validate_file(config.bgm, "BGM file")
    if config.audio_enabled:
        for key, sfx_path in config.sfx.items():
            _validate_file(sfx_path, f"SFX '{key}' file")

    return config
