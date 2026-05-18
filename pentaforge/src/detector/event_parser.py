"""Parse OCR or transcript text into League of Legends kill events."""

from dataclasses import dataclass
import re
from typing import Iterable


@dataclass(frozen=True)
class TextObservation:
    """A text snippet observed at a timestamp in the source video."""

    time: float
    text: str
    confidence: float = 1.0
    source: str = "ocr"


@dataclass(frozen=True)
class KillEvent:
    """A detected multi-kill event."""

    time: float
    kill_type: str
    text: str
    confidence: float = 1.0
    source: str = "ocr"


_KILL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("penta_kill", re.compile(r"(penta\s*kill|pentakill|五\s*杀|五殺)", re.I)),
    ("quadra_kill", re.compile(r"(quadra\s*kill|quadrakill|四\s*杀|四殺)", re.I)),
    ("triple_kill", re.compile(r"(triple\s*kill|triplekill|三\s*杀|三殺)", re.I)),
    ("double_kill", re.compile(r"(double\s*kill|doublekill|双\s*杀|雙殺)", re.I)),
]


def detect_kill_type(text: str) -> str | None:
    """Return a normalized kill type from recognized text, if present."""
    normalized = _normalize_text(text)
    for kill_type, pattern in _KILL_PATTERNS:
        if pattern.search(normalized):
            return kill_type
    return None


def parse_kill_events(
    observations: Iterable[TextObservation],
    *,
    min_confidence: float = 0.0,
    dedupe_window: float = 1.5,
) -> list[KillEvent]:
    """Convert OCR/transcript observations into de-duplicated kill events.

    OCR often sees the same banner across several sampled frames. Events with
    the same kill type inside ``dedupe_window`` seconds are collapsed into the
    highest-confidence observation.
    """
    candidates: list[KillEvent] = []
    for obs in observations:
        if obs.confidence < min_confidence:
            continue
        kill_type = detect_kill_type(obs.text)
        if not kill_type:
            continue
        candidates.append(
            KillEvent(
                time=float(obs.time),
                kill_type=kill_type,
                text=obs.text,
                confidence=float(obs.confidence),
                source=obs.source,
            )
        )

    candidates.sort(key=lambda event: event.time)
    events: list[KillEvent] = []
    for event in candidates:
        if (
            events
            and event.kill_type == events[-1].kill_type
            and event.time - events[-1].time <= dedupe_window
        ):
            if event.confidence > events[-1].confidence:
                events[-1] = event
            continue
        events.append(event)
    return events


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())
