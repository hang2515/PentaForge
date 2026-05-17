# PentaForge Web 可视化配置器 — 实施计划

## Context

用户需要一个 Web 界面来可视化配置 PentaForge 高光剪辑工具，替代手动编辑 YAML。核心需求：视频预览+时间轴打点、一键运行 Pipeline。技术栈：FastAPI 后端 + Vue 3 前端。

## 架构概览

```
浏览器 (localhost:5173 dev / localhost:8000 prod)
    │
    ├── REST API (/api/*) ──── FastAPI (src/server.py)
    ├── WebSocket (/ws/*) ──── 实时进度推送
    └── 静态文件 (/) ────────── Vue 3 构建产物 (static/)
```

后端复用现有 `src/pipeline.py`，新增 progress 回调版本。前端通过 Pinia store 管理全部配置状态，`js-yaml` 在客户端做 YAML ↔ JSON 互转。

## 文件结构

```
pentaforge/
├── src/
│   ├── server.py          [NEW] FastAPI 应用 + 所有 API 路由
│   └── pipeline.py        [MODIFY] 新增 run_pipeline_with_progress()
├── web/                   [NEW] Vue 3 + Vite 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── stores/config.js          Pinia store (全局配置状态)
│       ├── api/client.js             fetch 封装
│       └── components/
│           ├── VideoPreview.vue      <video> 播放器
│           ├── TimelineScrubber.vue  Canvas 时间轴 (核心难点)
│           ├── ConfigForm.vue        表单/YAML 双模式编辑器
│           ├── ClipEditor.vue        剪辑列表编辑
│           ├── AudioSettings.vue     BGM/SFX 设置
│           ├── TransitionSettings.vue
│           ├── ExportSettings.vue
│           ├── PipelineRunner.vue    运行按钮
│           └── ProgressOverlay.vue   进度弹窗
├── static/                [GENERATED] Vue build 输出
└── requirements.txt       [MODIFY] +fastapi, uvicorn, websockets
```

## API 设计

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/video/info?path=` | ffprobe 获取视频元信息 |
| GET | `/api/video/stream/{path}` | HTTP Range 流式播放视频 |
| POST | `/api/config/parse` | 验证 YAML 文本，返回 JSON |
| POST | `/api/config/save` | JSON 配置写回 YAML 文件 |
| POST | `/api/pipeline/run` | 启动 Pipeline，返回 job_id |
| WS | `/ws/progress/{job_id}` | 实时推送进度消息 |

### 消息格式

**WebSocket 服务端 → 客户端：**

```json
{"type": "step", "step": 1, "total": 4, "message": "Extracting clip 1/3..."}
{"type": "complete", "output_path": "/path/to/output.mp4"}
{"type": "error", "message": "FFmpeg error: ..."}
```

## 前端核心组件设计

### TimelineScrubber (最复杂的组件)
- Canvas 绘制横向时间轴，全长 = 视频时长
- 每个 clip 显示为彩色矩形，两端有拖拽手柄
- 播放头红线随 `<video>.currentTime` 实时移动
- 交互：点击空白区域→跳转、拖拽手柄→调整 start/end、Shift+点击→新建 clip、选中后 Delete→删除
- 60fps requestAnimationFrame 渲染循环

### 数据流
- Pinia store 是唯一状态源，所有组件直接读写 store
- 用户选择源视频 → store.source 变化 → 自动请求 `/api/video/info` → 更新时间轴
- 配置编辑 → store 实时更新 → 切换到 YAML 视图时用 `js-yaml` dump
- 点击运行 → POST config JSON → 获取 job_id → WebSocket 监听进度

## 实施步骤

### Step 1: 添加后端依赖 → verify: uvicorn 启动成功
- 更新 `requirements.txt`：fastapi, uvicorn[standard], websockets, python-multipart, aiofiles
- 安装依赖

### Step 2: FastAPI 骨架 + 健康检查 → verify: curl /api/health
- 创建 `src/server.py`：FastAPI app, CORS 中间件, /api/health 路由

### Step 3: 视频相关端点 → verify: curl 获取视频信息
- `/api/video/info` — 调用 ffmpeg.probe，返回 duration/width/height/fps/has_audio
- `/api/video/stream/{path}` — FileResponse 支持 Range 请求

### Step 4: 配置端点 → verify: YAML ↔ JSON 互转正确
- `/api/config/parse` — yaml.safe_load + 验证
- `/api/config/save` — dataclass → dict → yaml.dump

### Step 5: Pipeline 进度回调 → verify: 现有测试仍通过
- `src/pipeline.py` 新增 `run_pipeline_with_progress(config, callback)`
- 在提取/混音/复用/拼接各阶段调用 callback

### Step 6: WebSocket + Pipeline 运行端点 → verify: websocat 连接测试
- `POST /api/pipeline/run` — 后台线程运行 pipeline，返回 job_id
- `WS /ws/progress/{job_id}` — 订阅 job，推送进度 JSON

### Step 7: 前端脚手架 → verify: npm run dev 启动
- 创建 `web/` 目录，package.json, vite.config.js (dev proxy → :8000)
- `npm install` 安装 vue, pinia, js-yaml

### Step 8: Pinia Store + API Client → verify: 浏览器 console 调用 API
- `stores/config.js` — 完整配置状态
- `api/client.js` — fetch 封装

### Step 9: VideoPreview + TimelineScrubber → verify: 视频加载、时间轴渲染
- VideoPreview: `<video>` 绑定 store.source
- TimelineScrubber: Canvas 绘制，鼠标交互

### Step 10: ConfigForm + 子组件 → verify: 表单编辑 → YAML 输出一致
- 表单/YAML 双模式
- ClipEditor, AudioSettings, TransitionSettings, ExportSettings

### Step 11: PipelineRunner + ProgressOverlay → verify: 点击运行 → 看到进度
- 运行按钮 → WebSocket 连接 → 进度条 + 步骤日志

### Step 12: App.vue 总装 + 静态文件服务 → verify: 完整流程
- 双栏布局：左侧配置、右侧视频+时间轴
- server.py 挂载 static/ 目录

### Step 13: 验证 → verify: 24 现有测试 + 新增 API 测试 + 手工端到端
- `pytest tests/` 确保无回归
- 新增 `tests/test_server.py`
- 手工测试：选视频 → 打点 → 运行 → 输出文件

## 前提条件

- 用户需要安装 Node.js (仅开发/构建时需要，生产可用预构建的 static/)
- Python 依赖通过 venv + pip 安装

## 不做

- 不做用户认证（本地工具）
- 不做移动端适配（桌面工具）
- 不修改现有 CLI 行为
- 不重构现有 pipeline 逻辑（只加 progress 回调）
