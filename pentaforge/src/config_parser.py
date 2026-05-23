"""Parse and validate highlight configuration files."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Optional, Union

import yaml


@dataclass
class ClipConfig:
    start: float
    end: float
    kill_type: str = ""
    label: str = ""
    sfx_offset: Optional[float] = None
    bgm: Optional[str] = None
    source_index: int = 0

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class SourceConfig:
    path: str
    name: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = os.path.basename(self.path)


@dataclass
class TransitionConfig:
    type: str = "fade"
    duration: float = 0.6


@dataclass
class ExportConfig:
    resolution: str = "1920x1080"
    fps: int = 60
    codec: str = "libx264"
    bitrate: str = "12M"
    preset: str = "medium"


@dataclass
class PipelineConfig:
    source: str = ""  # kept for backward compat with old YAML
    output: str = ""
    clips: list[ClipConfig] = field(default_factory=list)
    sources: list[SourceConfig] = field(default_factory=list)
    bgm: str = ""
    bgm_volume: float = 0.3
    sfx: dict[str, str] = field(default_factory=dict)
    sfx_volume: float = 0.8
    audio_enabled: bool = True
    transitions: TransitionConfig = field(default_factory=TransitionConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    temp_dir: str = ""

    def source_for(self, clip: ClipConfig) -> str:
        """Resolve the source file path for a clip, handling both old and new formats."""
        idx = clip.source_index
        if 0 <= idx < len(self.sources):
            return self.sources[idx].path
        return self.source  # fallback for single-source YAML


_TIME_RE = re.compile(
    r"^(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)$"
)
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


def load_config(path: str) -> PipelineConfig:
    """Load and validate a YAML configuration file."""
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raise ValueError("Config file is empty")

    # Parse sources (new multi-source format) or fallback to single source
    sources_raw = raw.get("sources", [])
    if sources_raw:
        sources = [SourceConfig(path=s.get("path", ""), name=s.get("name", "")) for s in sources_raw]
    else:
        source = raw.get("source", "")
        if not source:
            raise ValueError("Missing required field: source")
        sources = [SourceConfig(path=source)]

    clips_raw = raw.get("clips", [])
    if not clips_raw:
        raise ValueError("No clips defined in config")

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

        si = int(c.get("source_index", 0))
        if si >= len(sources):
            si = 0

        clips.append(ClipConfig(
            start=start,
            end=end,
            kill_type=str(c.get("kill_type", "")),
            label=str(c.get("label", "")),
            sfx_offset=sfx_offset,
            bgm=c.get("bgm"),
            source_index=si,
        ))

    transitions_raw = raw.get("transitions", {})
    transitions = TransitionConfig(
        type=transitions_raw.get("type", "fade"),
        duration=float(transitions_raw.get("duration", 0.6)),
    )

    export_raw = raw.get("export", {})
    export = ExportConfig(
        resolution=export_raw.get("resolution", "1920x1080"),
        fps=int(export_raw.get("fps", 60)),
        codec=export_raw.get("codec", "libx264"),
        bitrate=export_raw.get("bitrate", "12M"),
        preset=export_raw.get("preset", "medium"),
    )

    config = PipelineConfig(
        source=sources[0].path if sources else "",
        sources=sources,
        output=raw.get("output", "highlight_output.mp4"),
        clips=clips,
        bgm=raw.get("bgm", ""),
        bgm_volume=float(raw.get("bgm_volume", 0.3)),
        sfx=raw.get("sfx", {}),
        sfx_volume=float(raw.get("sfx_volume", 0.8)),
        audio_enabled=bool(raw.get("audio_enabled", True)),
        transitions=transitions,
        export=export,
        temp_dir=raw.get("temp_dir", ""),
    )

    # Validate files exist
    for src in sources:
        _validate_file(src.path, "Source video")
    if config.bgm:
        _validate_file(config.bgm, "BGM file")
    for key, sfx_path in config.sfx.items():
        if sfx_path and not os.path.exists(sfx_path):
            import warnings
            warnings.warn(f"SFX '{key}' file not found: {sfx_path}")

    return config
