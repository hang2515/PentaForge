"""OCR adapter interfaces for Phase 2 detection.

PaddleOCR implements this small interface and feeds observations into
``event_parser.parse_kill_events``. Other engines can be added later without
changing the detection pipeline.
"""

from typing import Protocol

from .event_parser import TextObservation


class OcrReader(Protocol):
    """Protocol implemented by OCR backends."""

    def read_frame(self, image_path: str, *, timestamp: float) -> list[TextObservation]:
        """Return text observations found in a sampled frame."""
        ...
