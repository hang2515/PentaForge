# AGENT 中文版

本文件是 `AGENT.md` 的中文阅读版。每次修改 `AGENT.md` 时，都应同步更新本文件。
大模型优先读取英文版 `AGENT.md`；本文件主要面向人类阅读和团队沟通。

## 项目概览

PentaForge 是一个半自动的《英雄联盟》高光片段剪辑工具。

核心流程：

```text
录制视频 -> 高光检测 -> 片段提取 -> 音频处理 -> 拼接/转场 -> 最终导出
```

项目应保持在不使用 Docker 的情况下也可以运行。默认本地环境为：

- Python 虚拟环境：`.venv`
- Web UI 的 Node.js 依赖
- 基于 FFmpeg 的视频处理

## 当前技术栈

后端：

- Python 3.11+
- FastAPI
- Uvicorn
- WebSocket 进度更新
- `ffmpeg-python`
- `imageio-ffmpeg`
- PyYAML
- pytest

前端：

- Vue 3
- Vite
- Pinia
- js-yaml
- Node.js 20+

视频和音频：

- FFmpeg 是核心处理引擎。
- 模式 1 保留原始音频。
- 模式 2 使用 BGM/SFX 替换音频。
- 支持全局转场和每个片段的 `transition_after`。

OCR 和检测：

- PaddleOCR 是第二阶段自动检测的首选 OCR 引擎。
- OCR 依赖体积较大，应保持为可选依赖。
- OCR 失败时，必须保留手动编辑时间戳作为兜底方案。

配置：

- YAML 是面向用户的主要配置格式。
- JSON 可用于 API 请求体和 Web 内部状态。
- 配置路径应尽可能相对于配置文件所在位置解析。

## 本地环境命令

在仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -r .\pentaforge\requirements.txt
```

如果存在开发依赖文件，优先使用：

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\pentaforge\requirements-dev.txt
```

前端：

```powershell
cd .\pentaforge\web
npm install
cd ..\..
```

可选 OCR 依赖，存在 `requirements-ocr.txt` 时安装：

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\pentaforge\requirements-ocr.txt
```

## 开发命令

后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.server:app --app-dir .\pentaforge --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd .\pentaforge\web
npm run dev -- --host 127.0.0.1
```

测试：

```powershell
$env:PYTHONPATH = (Resolve-Path -LiteralPath .\pentaforge).Path
.\.venv\Scripts\python.exe -m pytest .\pentaforge\tests -q
```

前端构建：

```powershell
cd .\pentaforge\web
npm run build
```

## 代理行为规则

以下规则改编自 `CLAUDE.md`，适用于所有编码代理。

### 编码前先思考

- 不要默默假设。
- 如果请求有歧义，说明假设或提出简短问题。
- 如果存在多种理解，说明取舍。
- 如果有更简单的方案，应主动指出。
- 如果不明确到可能影响工作的程度，先停下来澄清。

### 简单优先

- 编写能解决请求的最少代码。
- 不添加推测性功能。
- 不为一次性逻辑创建抽象。
- 除非用户要求或代码库已有类似模式，否则不新增可配置项。
- 如果实现明显比必要复杂，完成前先简化。

### 精准修改

- 只修改完成请求所需的文件。
- 匹配现有代码风格。
- 不重构无关代码。
- 除非用户明确要求，不删除无关的废弃代码。
- 只有当自己的修改导致导入、变量或文件不再需要时，才移除它们。
- 每一行修改都应能追溯到用户请求。

### 以目标驱动执行

- 在大范围修改前定义成功标准。
- 行为变化时，添加或更新聚焦的测试。
- 可行时，在最终回复前运行相关测试或构建。
- 多步骤任务使用简短计划，并随着完成情况更新。

示例：

```text
1. 更新解析器 -> 用解析器测试验证
2. 更新 Web 表单 -> 用 npm build 验证
3. 更新文档 -> 验证路径和命令
```

## 前端规则

- 保留当前 Vue 3 + Vite 架构。
- 优先使用现有组件和 Pinia store 模式。
- UI 应保持实用，并足够紧凑以支持编辑工作流。
- 不要把应用改成营销落地页。
- 确保按钮、输入框和标签在小屏幕上能正常显示。
- 添加控件时，按需贯通 store、YAML 导入导出和 API 请求体。

## 后端规则

- 除非有明确理由，否则保持 FastAPI API 形状不变。
- 长时间运行的 FFmpeg/OCR 操作应尽可能通过进度更新可观测。
- 在解析器/API 边界校验配置输入。
- 用聚焦测试覆盖 FFmpeg 相关行为。
- 不要在已提交的配置或源码中硬编码本地绝对路径。

## 检测/OCR 规则

- PaddleOCR 是可选依赖，不应成为基础安装的必需项。
- 如果 OCR 不可用，API 应返回清晰的安装提示。
- OCR 生成的片段只是候选结果，不是最终事实。
- 用户必须能够在 OCR 检测后手动新增、删除和调整片段。
- 修改 ROI 默认值和采样间隔时，必须更新文档。

## 文档规则

- 保持 `AGENT.zh-CN.md` 与 `AGENT.md` 同步。
- 修改阶段性功能时，更新 `DESIGN.md`。
- 修改安装或启动命令时，更新本地环境文档。
- 添加配置字段时，更新：
  - 配置示例
  - 解析器测试
  - Web 表单行为
  - YAML 导入导出逻辑
- 如果功能只完成了一部分，标记为“基础版”或“进行中”，不要标记为“完成”。

## Git 工作流规则

- 不要直接在 `main` 上开发。
- 使用功能分支，例如：
  - `feature/paddleocr-background-job`
  - `feature/sfx-file-mapping`
  - `fix/audio-preserve-mode`
  - `docs/local-setup`
- 保持 `main` 稳定，并与 `origin/main` 同步。
- 将代码提交到目标功能分支，然后推送该分支。
- 提交前始终运行：

```bash
git status
```

- 不要提交运行时文件、日志、媒体文件、虚拟环境、构建产物或模型权重。
- 常规分支推送使用 `git push origin <branch>`。
- 除非明确约定，不要强制推送共享分支。

## 不应提交的文件

不要提交：

- `.venv/`
- `node_modules/`
- `pentaforge/static/`
- `__pycache__/`
- `.pytest_cache/`
- `*.log`
- `*.pid`
- `.env`
- 大型原始视频或音频文件
- 生成的输出视频
- OCR/模型缓存
- 模型权重文件，例如 `*.onnx`、`*.pdmodel`、`*.pdiparams`、`*.safetensors`

通常应提交的文件：

- `pentaforge/src/` 下的源代码
- `pentaforge/web/src/` 下的 Web 源码
- `pentaforge/tests/` 下的测试
- `requirements.txt`
- 存在时提交 `requirements-dev.txt`
- 存在时提交 `requirements-ocr.txt`
- `package.json`
- `package-lock.json`
- `DESIGN.md`
- 存在时提交 `LOCAL_SETUP.md`
- `AGENT.md`
- `AGENT.zh-CN.md`

## 安全规则

- 除非用户明确要求，绝不运行 `git reset --hard` 或强制推送等破坏性 Git 命令。
- 除非用户明确要求，绝不删除用户文件或媒体资产。
- 删除生成目录前，先确认路径位于仓库内部。
- 不要提交密钥、本地路径、API key 或个人机器状态。

## 最终回复前检查清单

- 修改是否直接回应了用户请求？
- 是否避免了无关重构？
- 是否运行了测试/构建，或说明了未运行原因？
- 是否需要更新文档或配置示例？
- `git status` 是否没有意外生成文件？
- 如果涉及 Git 操作，分支和推送说明是否清楚？
