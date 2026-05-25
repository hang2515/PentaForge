"""Tests for PaddleOCR result parsing helpers."""

from src.detector.paddleocr_reader import _iter_text_scores


def test_iter_text_scores_reads_paddle_v3_dict_result():
    result = {
        "res": {
            "rec_texts": ["Double Kill", "noise"],
            "rec_scores": [0.92, 0.31],
        }
    }

    assert list(_iter_text_scores(result)) == [("Double Kill", 0.92), ("noise", 0.31)]


def test_iter_text_scores_reads_legacy_result_shape():
    result = [[[[0, 0], [1, 0], [1, 1], [0, 1]], ("Triple Kill", 0.88)]]

    assert list(_iter_text_scores(result)) == [("Triple Kill", 0.88)]


def test_iter_text_scores_reads_result_json_property():
    class FakeResult:
        @property
        def json(self):
            return {"res": {"rec_texts": ["Penta Kill"], "rec_scores": [0.97]}}

    assert list(_iter_text_scores([FakeResult()])) == [("Penta Kill", 0.97)]
