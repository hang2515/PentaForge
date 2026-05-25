# AGENT.md

This file defines the project rules for AI coding agents working on PentaForge.
It incorporates the current `CLAUDE.md` guidance and adds project-specific
technical, workflow, documentation, and Git rules.

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

- PaddleOCR is the required OCR engine for Phase 2 automatic detection.
- OCR dependencies (paddlepaddle, paddleocr) are included in `requirements.txt`.
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


### Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.


### Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.


### Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

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

- PaddleOCR is a required dependency, installed with `requirements.txt`.
- If OCR fails to initialize, the API should fail with a clear error message.
- OCR-generated clips are candidates, not final truth.
- The user must be able to manually add, delete, and adjust clips after OCR detection.
- ROI defaults and sampling interval must be documented when changed.

## Documentation Rules

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
- `package.json`
- `package-lock.json`
- `DESIGN.md`
- `LOCAL_SETUP.md` when present
- `AGENT.md`

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
