"""Frame sampling and ROI extraction primitives for detector pipelines."""

from dataclasses import dataclass
import os

from .. import _ffmpeg_init  # noqa: F401 - patches ffmpeg binary lookup
import ffmpeg


@dataclass(frozen=True)
class Roi:
    """Region of interest expressed as fractions of frame size."""

    x: float
    y: float
    width: float
    height: float

    def to_pixels(self, frame_width: int, frame_height: int) -> tuple[int, int, int, int]:
        """Convert normalized ROI values to pixel crop parameters."""
        left = round(self.x * frame_width)
        top = round(self.y * frame_height)
        width = round(self.width * frame_width)
        height = round(self.height * frame_height)
        if width <= 0 or height <= 0:
            raise ValueError("ROI width and height must be positive")
        return left, top, width, height


def frame_sample_times(duration: float, interval: float = 0.5) -> list[float]:
    """Return timestamps to sample from a video duration."""
    if duration <= 0:
        return []
    if interval <= 0:
        raise ValueError("interval must be positive")
    times: list[float] = []
    current = 0.0
    while current < duration:
        times.append(round(current, 3))
        current += interval
    return times


def extract_frame(source: str, timestamp: float, output: str, roi: Roi | None = None) -> None:
    """Extract a single frame, optionally cropped to a normalized ROI."""
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    stream = ffmpeg.input(source, ss=max(0.0, timestamp))
    video = stream.video
    if roi is not None:
        info = ffmpeg.probe(source)
        video_stream = next(
            (item for item in info.get("streams", []) if item.get("codec_type") == "video"),
            None,
        )
        if not video_stream:
            raise ValueError("Source has no video stream")
        left, top, width, height = roi.to_pixels(
            int(video_stream["width"]),
            int(video_stream["height"]),
        )
        video = video.filter("crop", width, height, left, top)

    ffmpeg.run(
        ffmpeg.output(video, output, vframes=1).global_args("-y"),
        capture_stdout=True,
        capture_stderr=True,
    )
