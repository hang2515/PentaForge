# AGENT.md

This file defines the project rules for AI coding agents working on PentaForge.
It incorporates the current `CLAUDE.md` guidance and adds project-specific
technical, workflow, documentation, and Git rules.

For human-readable Chinese documentation, keep `AGENT.zh-CN.md` synchronized
with this file whenever these rules change.

## Project Overview

PentaForge is a semi-automatic League of Legends highlight clipping tool.

Core workflow:

```text
recording video -> highlight detection -> clip extraction -> audio processing -> stitching/transitions -> final export
```

The project should remain usable without Docker. The default local setup is:

- Python virtual environment: `.venv`
- Node.js dependencies for the Web UI
- FFmpeg-based video processing

## Current Technology Stack

Backend:

- Python 3.11+
- FastAPI
- Uvicorn
- WebSocket progress updates
- `ffmpeg-python`
- `imageio-ffmpeg`
- PyYAML
- pytest

Frontend:

- Vue 3
- Vite
- Pinia
- js-yaml
- Node.js 20+

Video and audio:

- FFmpeg is the core processing engine.
- Mode 1 keeps original audio.
- Mode 2 replaces audio with BGM/SFX.
- Global transitions and per-clip `transition_after` are supported.

OCR and detection:

- PaddleOCR is the preferred OCR engine for Phase 2 automatic detection.
- OCR dependencies should stay optional because they are large.
- Manual timestamp editing must remain available as the fallback when OCR fails.

Configuration:

- YAML is the primary user-facing config format.
- JSON may be supported for API payloads and internal Web state.
- Config paths should resolve relative to the config file location when possible.

## Local Setup Commands

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -r .\pentaforge\requirements.txt
```

If a development requirements file exists, prefer it:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\pentaforge\requirements-dev.txt
```

Frontend:

```powershell
cd .\pentaforge\web
npm install
cd ..\..
```

Optional OCR dependencies, when `requirements-ocr.txt` exists:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\pentaforge\requirements-ocr.txt
```

## Development Commands

Backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.server:app --app-dir .\pentaforge --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd .\pentaforge\web
npm run dev -- --host 127.0.0.1
```

Tests:

```powershell
$env:PYTHONPATH = (Resolve-Path -LiteralPath .\pentaforge).Path
.\.venv\Scripts\python.exe -m pytest .\pentaforge\tests -q
```

Frontend build:

```powershell
cd .\pentaforge\web
npm run build
```

## Agent Behavior Rules

These rules are adapted from `CLAUDE.md` and apply to all coding agents.

### Think Before Coding

- Do not assume silently.
- If the request is ambiguous, state assumptions or ask a concise question.
- If multiple interpretations exist, name the tradeoff.
- If a simpler approach exists, point it out.
- If something is unclear enough to risk the work, stop and clarify.

### Simplicity First

- Write the minimum code that solves the request.
- Do not add speculative features.
- Do not create abstractions for one-off logic.
- Do not add configurability unless the user asked for it or the codebase already uses it.
- If the implementation becomes much larger than necessary, simplify before finishing.

### Surgical Changes

- Touch only files required for the request.
- Match the existing style.
- Do not refactor unrelated code.
- Do not delete unrelated dead code unless explicitly asked.
- Remove imports, variables, or files only when your own changes made them obsolete.
- Every changed line should trace back to the user request.

### Goal-Driven Execution

- Define what success means before broad changes.
- Add or update focused tests when behavior changes.
- Run relevant tests/builds before finalizing when feasible.
- For multi-step work, use a brief plan and update it as work completes.

Example:

```text
1. Update parser -> verify with parser tests
2. Update Web form -> verify with npm build
3. Update docs -> verify paths and commands
```

## Frontend Rules

- Preserve the current Vue 3 + Vite architecture.
- Prefer existing components and Pinia store patterns.
- Keep the UI functional and dense enough for editing workflows.
- Do not turn the app into a marketing landing page.
- Ensure buttons, inputs, and labels fit on small screens.
- When adding controls, wire them through the store, YAML export/import, and API payloads as needed.

## Backend Rules

- Preserve the FastAPI API shape unless there is a clear reason to change it.
- Keep long-running FFmpeg/OCR operations observable through progress updates when possible.
- Validate config inputs at the parser/API boundary.
- Keep FFmpeg-related behavior covered by focused tests.
- Do not hard-code local absolute paths in committed configs or source.

## Detection/OCR Rules

- PaddleOCR is optional and should not be required for the base install.
- If OCR is unavailable, the API should fail with a clear install message.
- OCR-generated clips are candidates, not final truth.
- The user must be able to manually add, delete, and adjust clips after OCR detection.
- ROI defaults and sampling interval must be documented when changed.

## Documentation Rules

- Keep `AGENT.zh-CN.md` synchronized with `AGENT.md`.
- When changing a phase feature, update `DESIGN.md`.
- When changing install/start commands, update local setup documentation.
- When adding config fields, update:
  - config examples
  - parser tests
  - Web form behavior
  - YAML import/export logic
- If a feature is only partially complete, mark it as "basic version" or "in progress" instead of "complete".

## Git Workflow Rules

- Do not develop directly on `main`.
- Use feature branches such as:
  - `feature/paddleocr-background-job`
  - `feature/sfx-file-mapping`
  - `fix/audio-preserve-mode`
  - `docs/local-setup`
- Keep `main` stable and synchronized with `origin/main`.
- Commit code to the intended feature branch, then push that branch.
- Before committing, always run:

```bash
git status
```

- Do not commit runtime files, logs, media, virtual environments, build output, or model weights.
- Use `git push origin <branch>` for normal branch pushes.
- Do not force-push shared branches unless explicitly agreed.

## Files That Should Not Be Committed

Do not commit:

- `.venv/`
- `node_modules/`
- `pentaforge/static/`
- `__pycache__/`
- `.pytest_cache/`
- `*.log`
- `*.pid`
- `.env`
- large raw videos or audio files
- generated output videos
- OCR/model caches
- model weight files such as `*.onnx`, `*.pdmodel`, `*.pdiparams`, `*.safetensors`

Files that usually should be committed:

- Source code under `pentaforge/src/`
- Web source under `pentaforge/web/src/`
- Tests under `pentaforge/tests/`
- `requirements.txt`
- `requirements-dev.txt` when present
- `requirements-ocr.txt` when present
- `package.json`
- `package-lock.json`
- `DESIGN.md`
- `LOCAL_SETUP.md` when present
- `AGENT.md`
- `AGENT.zh-CN.md`

## Safety Rules

- Never run destructive Git commands such as `git reset --hard` or force-push unless the user explicitly asks.
- Never delete user files or media assets unless the user explicitly asks.
- Before removing generated directories, verify the path is inside the repository.
- Do not commit secrets, local paths, API keys, or personal machine state.

## Review Checklist Before Final Response

- Did the change directly answer the user's request?
- Did it avoid unrelated refactors?
- Did tests/builds run, or is the reason for not running them stated?
- Did docs/config examples need updates?
- Is `git status` free of unexpected generated files?
- Are branch and push instructions clear if Git work was involved?
