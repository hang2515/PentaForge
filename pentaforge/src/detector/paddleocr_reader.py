"""PaddleOCR-backed implementation of the OCR reader protocol."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .event_parser import TextObservation


class PaddleOcrReader:
    """Read sampled frame images with PaddleOCR."""

    def __init__(
        self,
        *,
        lang: str = "ch",
        confidence_floor: float = 0.0,
        **kwargs: Any,
    ) -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR is not installed. Run "
                "`python -m pip install -r pentaforge/requirements-ocr.txt` "
                "inside the project virtual environment."
            ) from exc

        options = {
            "lang": lang,
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
        }
        options.update(kwargs)
        self._ocr = PaddleOCR(**options)
        self._confidence_floor = confidence_floor

    def read_frame(self, image_path: str, *, timestamp: float) -> list[TextObservation]:
        results = self._predict(image_path)
        observations: list[TextObservation] = []
        for text, confidence in _iter_text_scores(results):
            if confidence < self._confidence_floor:
                continue
            observations.append(
                TextObservation(
                    time=timestamp,
                    text=text,
                    confidence=confidence,
                    source="paddleocr",
                )
            )
        return observations

    def _predict(self, image_path: str) -> Any:
        if hasattr(self._ocr, "predict"):
            return self._ocr.predict(input=image_path)
        return self._ocr.ocr(image_path, cls=False)


def _iter_text_scores(value: Any) -> Iterable[tuple[str, float]]:
    """Yield text/confidence pairs from PaddleOCR v3 or legacy result shapes."""
    if value is None:
        return

    if isinstance(value, dict):
        data = value.get("res") if isinstance(value.get("res"), dict) else value
        texts = data.get("rec_texts") or data.get("texts")
        scores = data.get("rec_scores") or data.get("scores")
        if isinstance(texts, list):
            for index, text in enumerate(texts):
                score = scores[index] if isinstance(scores, list) and index < len(scores) else 1.0
                yield str(text), _coerce_score(score)
            return

        for item in data.values():
            yield from _iter_text_scores(item)
        return

    json_data = _result_json(value)
    if json_data is not None:
        yield from _iter_text_scores(json_data)
        return

    if isinstance(value, (str, bytes)):
        return

    if isinstance(value, (list, tuple)):
        if len(value) >= 2 and isinstance(value[0], str):
            yield value[0], _coerce_score(value[1])
            return
        if len(value) >= 2 and isinstance(value[1], tuple) and len(value[1]) >= 2:
            yield str(value[1][0]), _coerce_score(value[1][1])
            return
        for item in value:
            yield from _iter_text_scores(item)


def _result_json(value: Any) -> Any | None:
    json_value = getattr(value, "json", None)
    if json_value is None:
        return None
    if callable(json_value):
        return json_value()
    return json_value


def _coerce_score(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
