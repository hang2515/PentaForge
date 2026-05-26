"""FastAPI server for PentaForge web configurator."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import uuid
from dataclasses import asdict, is_dataclass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import _ffmpeg_init  # noqa — init bundled FFmpeg binary (patches ffmpeg.run/probe)
import ffmpeg
from .config_parser import PipelineConfig, ClipConfig, TransitionConfig, ExportConfig, SourceConfig, load_config, parse_time
from .detector import (
    Roi,
    TextObservation,
    detect_candidates_from_video,
    events_to_clip_configs,
    events_to_penta_clip_configs,
    parse_kill_events,
)
from .pipeline import run_pipeline, run_pipeline_with_progress, PipelineResult

# ── FastAPI app ────────────────────────────────────────────────────────
app = FastAPI(title="PentaForge", version="1.0.0")

# Workspace root: the directory from which the server was started
WORKSPACE_ROOT = os.getcwd()
YAML_DIR = os.path.join(os.environ.get("APPDATA", WORKSPACE_ROOT), "PentaForge", "configs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── helpers ─────────────────────────────────────────────────────────────

def _dictify(obj):
    """Recursively convert dataclasses to plain dicts."""
    if is_dataclass(obj):
        return {k: _dictify(v) for k, v in asdict(obj).items()}
    if isinstance(obj, (list, tuple)):
        return [_dictify(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _dictify(v) for k, v in obj.items()}
    return obj


def _config_from_dict(d: dict) -> PipelineConfig:
    """Build PipelineConfig from JSON dict."""
    # Parse sources (new multi-source format) or fallback to single source
    sources_raw = d.get("sources", [])
    if sources_raw:
        sources = [SourceConfig(path=s.get("path", ""), name=s.get("name", "")) for s in sources_raw]
    else:
        source = d.get("source", "")
        sources = [SourceConfig(path=source)] if source else []

    t_raw = d.get("transitions", {})
    transitions = TransitionConfig(
        type=t_raw.get("type", "fade"),
        duration=float(t_raw.get("duration", 0.6)),
    )
    clips = [
        ClipConfig(
            start=parse_time(c["start"]),
            end=parse_time(c["end"]),
            kill_type=c.get("kill_type", ""),
            label=c.get("label", ""),
            sfx_offset=c.get("sfx_offset"),
            bgm=c.get("bgm"),
            source_index=int(c.get("source_index", 0)),
            transition_after=_transition_from_dict(c.get("transition_after"), transitions) if "transition_after" in c else None,
        )
        for c in d.get("clips", [])
    ]
    e_raw = d.get("export", {})
    export = ExportConfig(
        resolution=e_raw.get("resolution", "1920x1080"),
        fps=int(e_raw.get("fps", 60)),
        codec=e_raw.get("codec", "libx264"),
        bitrate=e_raw.get("bitrate", "12M"),
        preset=e_raw.get("preset", "medium"),
    )
    return PipelineConfig(
        source=sources[0].path if sources else (d.get("source", "")),
        sources=sources,
        output=d.get("output", "highlight_output.mp4"),
        clips=clips,
        bgm=d.get("bgm", ""),
        bgm_volume=float(d.get("bgm_volume", 0.3)),
        sfx=d.get("sfx", {}),
        sfx_volume=float(d.get("sfx_volume", 0.8)),
        audio_enabled=_parse_bool(d.get("audio_enabled"), False),
        transitions=transitions,
        export=export,
        temp_dir=d.get("temp_dir", ""),
    )


def _transition_from_dict(raw, default):
    if raw is None:
        return TransitionConfig(type=default.type, duration=default.duration)
    return TransitionConfig(
        type=raw.get("type", default.type),
        duration=float(raw.get("duration", default.duration)),
    )


def _parse_bool(raw, default=False):
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    value = str(raw).strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {raw!r}")


# ── job state ───────────────────────────────────────────────────────────

_jobs: dict[str, dict] = {}

# ── file dialog ───────────────────────────────────────────────────────────

@app.post("/api/file-dialog")
def open_file_dialog(body: dict = {}):
    """Open native OS file picker and return the selected path."""
    import tkinter as tk
    from tkinter import filedialog
    filetypes = body.get("filetypes", [])
    if not filetypes:
        filetypes = [("Video files", "*.mp4 *.avi *.mkv *.mov *.webm *.flv"),
                     ("Audio files", "*.mp3 *.wav *.m4a *.aac *.ogg *.flac"),
                     ("All files", "*.*")]
    initialdir = body.get("initialdir", "")
    if initialdir:
        initialdir = os.path.normpath(initialdir)
        if not os.path.isdir(initialdir):
            os.makedirs(initialdir, exist_ok=True)
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    kwargs = {
        "title": body.get("title", "选择文件"),
        "filetypes": [(t[0], t[1]) if isinstance(t, (list, tuple)) else t for t in filetypes],
    }
    if initialdir:
        kwargs["initialdir"] = initialdir
    paths = filedialog.askopenfilenames(**kwargs)
    root.destroy()
    if not paths:
        return {"paths": [], "cancelled": True}
    return {"paths": list(paths), "cancelled": False}


@app.post("/api/save-dialog")
def open_save_dialog(body: dict = {}):
    """Open native OS save dialog and return the chosen path."""
    import tkinter as tk
    from tkinter import filedialog
    initialdir = body.get("initialdir", "")
    if initialdir:
        initialdir = os.path.normpath(initialdir)
        if not os.path.isdir(initialdir):
            os.makedirs(initialdir, exist_ok=True)
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    kwargs = {
        "title": body.get("title", "保存文件"),
        "defaultextension": body.get("defaultextension", ".mp4"),
        "filetypes": body.get("filetypes", [("MP4 Video", "*.mp4"), ("All files", "*.*")]),
        "initialfile": body.get("filename", "highlight_output.mp4"),
    }
    if initialdir:
        kwargs["initialdir"] = initialdir
    path = filedialog.asksaveasfilename(**kwargs)
    root.destroy()
    if not path:
        return {"path": "", "cancelled": True}
    return {"path": path, "cancelled": False}


# ── REST endpoints ──────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/workspace")
def workspace_info():
    return {"root": WORKSPACE_ROOT, "yaml_dir": YAML_DIR}


@app.get("/api/video/info")
def video_info(path: str = Query(..., description="Path to video file")):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    try:
        info = ffmpeg.probe(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to probe video: {e}")
    duration = float(info.get("format", {}).get("duration", 0))
    video_stream = None
    has_audio = False
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and video_stream is None:
            video_stream = s
        if s.get("codec_type") == "audio":
            has_audio = True
    fps = 30.0
    if video_stream:
        fps_str = video_stream.get("r_frame_rate", "30/1")
        num, den = fps_str.split("/")
        fps = float(num) / float(den) if float(den) != 0 else 30.0
    return {
        "duration": duration,
        "width": video_stream.get("width", 0) if video_stream else 0,
        "height": video_stream.get("height", 0) if video_stream else 0,
        "fps": fps,
        "has_audio": has_audio,
    }


@app.get("/api/video/stream/{path:path}")
def video_stream(path: str):
    full = os.path.abspath(path)
    if not os.path.exists(full):
        raise HTTPException(status_code=404, detail=f"File not found: {full}")
    if not os.path.isfile(full):
        raise HTTPException(status_code=400, detail="Not a regular file")
    return FileResponse(full, media_type="video/mp4")


@app.post("/api/config/parse")
def config_parse(body: dict):
    yaml_text = body.get("yaml_text", "")
    if not yaml_text.strip():
        raise HTTPException(status_code=400, detail="Empty YAML text")
    try:
        raw = yaml.safe_load(yaml_text)
        if raw is None:
            raise HTTPException(status_code=400, detail="YAML parsed as empty")
        config = _config_from_dict(raw)
        return _dictify(config)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML parse error: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/config/save")
def config_save(body: dict):
    output_path = body.get("output_path", "")
    if not output_path:
        raise HTTPException(status_code=400, detail="Missing output_path")
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    try:
        yaml_text = body.get("yaml_text", "")
        if yaml_text:
            content = yaml_text
        else:
            config_dict = body.get("config", body)
            content = yaml.dump(config_dict, allow_unicode=True, default_flow_style=False, sort_keys=False)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"saved_path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/load")
def config_load(path: str = Query(...)):
    if not path:
        raise HTTPException(status_code=400, detail="Missing path")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Config file not found")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {"yaml_text": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/detector/candidates")
def detector_candidates(body: dict):
    """Generate editable clip candidates from recognized text observations."""
    observations_raw = body.get("observations", [])
    if not isinstance(observations_raw, list):
        raise HTTPException(status_code=400, detail="observations must be a list")

    try:
        observations = [
            TextObservation(
                time=parse_time(item["time"]),
                text=str(item["text"]),
                confidence=float(item.get("confidence", 1.0)),
                source=str(item.get("source", "manual")),
            )
            for item in observations_raw
        ]
        events = parse_kill_events(
            observations,
            min_confidence=float(body.get("min_confidence", 0.0)),
            dedupe_window=float(body.get("dedupe_window", 1.5)),
        )
        clips = events_to_clip_configs(
            events,
            pre_roll=float(body.get("pre_roll", 8.0)),
            post_roll=float(body.get("post_roll", 4.0)),
            merge_gap=float(body.get("merge_gap", 2.0)),
            video_duration=body.get("video_duration"),
        )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Observation missing field: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "events": [_dictify(event) for event in events],
        "clips": [_dictify(clip) for clip in clips],
    }


@app.post("/api/detector/video")
def detector_video(body: dict):
    """Run PaddleOCR over sampled video frames and return editable candidates."""
    source = body.get("source", "")
    if not source:
        raise HTTPException(status_code=400, detail="Missing source video path")

    roi_raw = body.get("roi") or {}
    roi = Roi(
        x=float(roi_raw.get("x", 0.2)),
        y=float(roi_raw.get("y", 0.06)),
        width=float(roi_raw.get("width", 0.6)),
        height=float(roi_raw.get("height", 0.24)),
    )

    try:
        result = detect_candidates_from_video(
            source,
            roi=roi,
            interval=float(body.get("interval", 0.5)),
            pre_roll=float(body.get("pre_roll", 8.0)),
            post_roll=float(body.get("post_roll", 4.0)),
            merge_gap=float(body.get("merge_gap", 2.0)),
            min_confidence=float(body.get("min_confidence", 0.0)),
            dedupe_window=float(body.get("dedupe_window", 1.5)),
            max_frames=body.get("max_frames"),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "observations": [_dictify(obs) for obs in result.observations],
        "events": [_dictify(event) for event in result.events],
        "clips": [_dictify(clip) for clip in result.clips],
        "duration": result.duration,
    }


@app.post("/api/detector/penta-export")
async def detector_penta_export(body: dict):
    """Detect penta-kill chains with OCR and start an export job."""
    source = body.get("source", "")
    if not source:
        raise HTTPException(status_code=400, detail="Missing source video path")

    roi_raw = body.get("roi") or {}
    roi = Roi(
        x=float(roi_raw.get("x", 0.2)),
        y=float(roi_raw.get("y", 0.06)),
        width=float(roi_raw.get("width", 0.6)),
        height=float(roi_raw.get("height", 0.24)),
    )

    try:
        result = detect_candidates_from_video(
            source,
            roi=roi,
            interval=float(body.get("interval", 0.5)),
            min_confidence=float(body.get("min_confidence", 0.3)),
            dedupe_window=float(body.get("dedupe_window", 1.5)),
            max_frames=body.get("max_frames"),
        )
        clips = events_to_penta_clip_configs(
            result.events,
            pre_double_roll=float(body.get("pre_double_roll", 15.0)),
            post_penta_roll=float(body.get("post_penta_roll", 3.0)),
            chain_gap=float(body.get("chain_gap", 12.0)),
            merge_gap=float(body.get("merge_gap", 2.0)),
            video_duration=result.duration,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not clips:
        return {
            "job_id": None,
            "observations": [_dictify(obs) for obs in result.observations],
            "events": [_dictify(event) for event in result.events],
            "clips": [],
            "duration": result.duration,
            "message": "No penta-kill chain detected; export was not started.",
        }

    config = _config_from_dict({
        "source": source,
        "output": body.get("output", "highlight_penta.mp4"),
        "clips": [_dictify(clip) for clip in clips],
        "bgm": body.get("bgm", ""),
        "bgm_volume": body.get("bgm_volume", 0.3),
        "sfx": body.get("sfx", {}),
        "sfx_volume": body.get("sfx_volume", 0.8),
        "audio_enabled": body.get("audio_enabled", False),
        "transitions": body.get("transitions", {}),
        "export": body.get("export", {}),
        "temp_dir": body.get("temp_dir", ""),
    })
    job_id = _start_pipeline_job(config, asyncio.get_running_loop())
    return {
        "job_id": job_id,
        "observations": [_dictify(obs) for obs in result.observations],
        "events": [_dictify(event) for event in result.events],
        "clips": [_dictify(clip) for clip in clips],
        "duration": result.duration,
    }


@app.post("/api/pipeline/run")
async def pipeline_run(body: dict):
    config = _config_from_dict(body)
    job_id = _start_pipeline_job(config, asyncio.get_running_loop())
    return {"job_id": job_id}


def _start_pipeline_job(config: PipelineConfig, loop) -> str:
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {"status": "running", "progress": [], "result": None}

    def _run():
        def cb(step, total, message):
            data = {"type": "step", "step": step, "total": total, "message": message}
            _jobs[job_id]["progress"].append(data)
            for ws in _subscribers.get(job_id, set()):
                try:
                    asyncio.run_coroutine_threadsafe(ws.send_json(data), loop)
                except Exception:
                    pass

        try:
            result = run_pipeline_with_progress(config, cb)
            _jobs[job_id]["status"] = "completed" if result.success else "error"
            _jobs[job_id]["result"] = _dictify(result)
            msg = {"type": "complete" if result.success else "error", "output_path": result.output_path, "errors": result.errors}
            for ws in _subscribers.get(job_id, set()):
                try:
                    asyncio.run_coroutine_threadsafe(ws.send_json(msg), loop)
                except Exception:
                    pass
        except Exception as e:
            _jobs[job_id]["status"] = "error"
            msg = {"type": "error", "message": str(e)}
            for ws in _subscribers.get(job_id, set()):
                try:
                    asyncio.run_coroutine_threadsafe(ws.send_json(msg), loop)
                except Exception:
                    pass

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return job_id


@app.get("/api/pipeline/status/{job_id}")
def pipeline_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": job["status"], "progress": job["progress"]}


# ── WebSocket ───────────────────────────────────────────────────────────

_subscribers: dict[str, set[WebSocket]] = {}


@app.websocket("/ws/progress/{job_id}")
async def ws_progress(ws: WebSocket, job_id: str):
    await ws.accept()
    _subscribers.setdefault(job_id, set()).add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _subscribers.get(job_id, set()).discard(ws)


# ── static files (production build) ─────────────────────────────────────

_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(os.path.join(_static_dir, "index.html")):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
