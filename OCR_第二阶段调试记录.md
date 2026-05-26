# OCR 第二阶段调试记录

日期：2026-05-26

## 目标

完成第二阶段 OCR 识别链路的调试准备与问题梳理，尽量不改动第一阶段 FFmpeg 剪辑流水线代码。

第二阶段目标链路：

```text
视频文件
  -> 按固定间隔抽帧
  -> 裁剪击杀播报 ROI
  -> PaddleOCR 识别文字
  -> 解析双杀/三杀/四杀/五杀事件
  -> 生成候选剪辑片段
  -> 保留人工修正入口
```

## 本次检查范围

只检查和记录第二阶段 OCR 相关文件：

- `pentaforge/src/detector/frame_sampler.py`
- `pentaforge/src/detector/ocr_reader.py`
- `pentaforge/src/detector/paddleocr_reader.py`
- `pentaforge/src/detector/event_parser.py`
- `pentaforge/src/detector/boundary.py`
- `pentaforge/src/detector/detect_pipeline.py`
- `pentaforge/src/server.py` 中的 `/api/detector/*` 接口
- `pentaforge/web/src/components/DetectionPanel.vue`
- `pentaforge/tests/test_detector_*.py`

第一阶段剪辑流水线文件暂不作为修改对象：

- `pentaforge/src/clip_extractor.py`
- `pentaforge/src/audio_processor.py`
- `pentaforge/src/clip_stitcher.py`
- `pentaforge/src/pipeline.py`

## 当前链路现状

### 后端入口

当前已有接口：

```text
POST /api/detector/video
```

接口会调用：

```text
detect_candidates_from_video()
  -> frame_sample_times()
  -> extract_frame()
  -> PaddleOcrReader.read_frame()
  -> parse_kill_events()
  -> events_to_clip_configs()
```

返回内容包含：

- `observations`：OCR 原始识别文本
- `events`：解析出的击杀事件
- `clips`：候选剪辑片段

### 默认 OCR 参数

当前默认 ROI：

```python
Roi(x=0.2, y=0.06, width=0.6, height=0.24)
```

当前默认采样间隔：

```text
interval = 0.5s
```

当前默认候选片段边界：

```text
pre_roll = 8.0s
post_roll = 4.0s
merge_gap = 2.0s
```

注意：这套默认值是通用候选片段规则，不是“一键五杀成片”的最终规则。

## 已确认的问题

### 1. 事件解析需要保持真实中文字符

`event_parser.py` 中当前应支持真实中文：

```text
双杀、三杀、四杀、五杀
雙殺、三殺、四殺、五殺
Double Kill、Triple Kill、Quadra Kill、Penta Kill、Pentakill
```

调试重点：

- 确认源码和测试文件统一用 UTF-8 打开与保存。
- 确认终端输出乱码不代表文件内容一定乱码。
- 如果测试失败，优先检查文件编码和正则匹配文本。

### 2. 当前边界算法还不是五杀链算法

`events_to_clip_configs()` 当前逻辑是“每个事件生成窗口，再合并相近窗口”。

这适合半自动候选，但不完全符合五杀链需求：

```text
clip_start = double_kill_time - 15s
clip_end = penta_kill_time + 3s
```

五杀链还需要：

- 按时间把多杀事件分链。
- 相邻事件间隔不超过 `chain_gap = 12s`。
- 只对包含 `penta_kill` 的链生成片段。
- 链内有 `double_kill` 时从双杀回退。
- 链内没有 `double_kill` 时从链内最早事件回退。
- 多个非常接近或重叠的五杀片段需要合并。

### 3. 一键五杀导出接口尚未单独落地

方案文档里规划了：

```text
POST /api/detector/penta-export
```

当前已有 `/api/detector/video`，但它只返回候选，不会自动启动导出任务。

后续如果实现一键导出，应保持第一阶段 pipeline 不变，只在第二阶段新增接口组装 `PipelineConfig` 后调用现有导出函数。

### 4. 前端检测面板已有半自动 OCR 入口

`DetectionPanel.vue` 已支持：

- 配置采样间隔
- 配置最大帧数
- 配置 ROI
- 配置置信度
- 调用 `/api/detector/video`
- 展示识别事件和候选片段
- 把候选片段添加到手动片段

这符合“手动修正作为 fallback”的要求。

## 建议调试顺序

### Step 1：事件解析单测

目标：先证明 OCR 文本能被解析为标准事件。

建议验证：

```text
双杀 -> double_kill
三杀 -> triple_kill
四杀 -> quadra_kill
五杀 -> penta_kill
雙殺 -> double_kill
五殺 -> penta_kill
Double Kill -> double_kill
Penta Kill -> penta_kill
Pentakill -> penta_kill
```

成功标准：

```text
test_detector_event_parser.py 通过
```

### Step 2：五杀链边界单测

目标：新增或验证五杀链算法，不影响原有通用候选算法。

建议输入：

```text
130.0 双杀
135.0 三杀
140.0 四杀
144.0 五杀
```

期望输出：

```text
start = 115.0
end = 147.0
kill_type = penta_kill
```

成功标准：

```text
test_detector_boundary.py 新增五杀链用例通过
```

### Step 3：PaddleOCR 结果结构兼容测试

目标：确认 `paddleocr_reader.py` 可以解析 PaddleOCR v3 和旧版结果结构。

重点函数：

```text
_iter_text_scores()
```

成功标准：

```text
test_detector_paddleocr_reader.py 通过
```

### Step 4：视频抽帧链路测试

目标：不用真实 OCR，先用 fake reader 验证抽帧、时间戳、候选生成链路。

成功标准：

```text
test_detector_detect_pipeline.py 通过
```

### Step 5：真实视频小样本调试

目标：用短视频或 `max_frames` 限制验证真实 PaddleOCR。

建议参数：

```json
{
  "interval": 0.5,
  "max_frames": 60,
  "min_confidence": 0.3,
  "roi": {
    "x": 0.2,
    "y": 0.06,
    "width": 0.6,
    "height": 0.24
  }
}
```

观察项：

- `observations` 是否有击杀播报文本。
- `events` 是否能识别到标准 kill type。
- `clips` 是否产生可手动修正的候选片段。
- 如果 `observations` 为空，优先调 ROI 和采样间隔。
- 如果 `observations` 有文本但 `events` 为空，优先调事件解析规则。

## 推荐执行命令

从项目根目录执行：

```powershell
$env:PYTHONPATH = (Resolve-Path -LiteralPath .\pentaforge).Path
.\.venv\Scripts\python.exe -m pytest .\pentaforge\tests\test_detector_event_parser.py -q
.\.venv\Scripts\python.exe -m pytest .\pentaforge\tests\test_detector_boundary.py -q
.\.venv\Scripts\python.exe -m pytest .\pentaforge\tests\test_detector_paddleocr_reader.py -q
.\.venv\Scripts\python.exe -m pytest .\pentaforge\tests\test_detector_detect_pipeline.py -q
```

如果需要跑完整测试：

```powershell
$env:PYTHONPATH = (Resolve-Path -LiteralPath .\pentaforge).Path
.\.venv\Scripts\python.exe -m pytest .\pentaforge\tests -q
```

## 下一步改动建议

优先级从高到低：

1. 保留现有 `events_to_clip_configs()`，新增独立 `events_to_penta_clip_configs()`。
2. 为五杀链算法补测试，不复用通用候选片段测试代替。
3. 在 `/api/detector/video` 中继续返回通用候选，避免破坏现有半自动流程。
4. 新增 `/api/detector/penta-export` 时，只新增第二阶段接口，不改第一阶段剪辑实现。
5. 前端新增“一键识别五杀并导出”按钮时，继续保留“从当前视频自动识别”和“添加全部到手动片段”。

## 当前结论

第二阶段 OCR 的基础链路已经存在，当前调试重点不是第一阶段剪辑，而是：

- OCR 识别文本是否能稳定进入 `observations`
- 中文/英文多杀文本是否能正确解析为 `KillEvent`
- 五杀链是否有独立边界算法
- 一键导出是否作为新增入口接入现有 pipeline

以上内容是实施前的 OCR 第二阶段调试梳理；后续小节记录实际代码变更和验证结果。

## 2026-05-26 实施记录

本次已按上面的调试计划完成第二阶段 OCR 相关代码改动，未修改第一阶段 FFmpeg 剪辑流水线内部实现。

### 已完成代码改动

1. 新增五杀链边界算法。

修改文件：

```text
pentaforge/src/detector/boundary.py
```

新增函数：

```text
events_to_penta_clip_configs()
```

实现规则：

- 按时间顺序把多杀事件分链。
- 相邻事件间隔大于 `chain_gap` 时开启新链。
- 只对包含 `penta_kill` 的链生成剪辑片段。
- 链内存在 `double_kill` 时，从双杀时间前推 `pre_double_roll`。
- 链内不存在 `double_kill` 时，从链内最早事件前推 `pre_double_roll`。
- 片段结束时间为链内最后一个 `penta_kill` 后推 `post_penta_roll`。
- 使用 `video_duration` 裁剪片段结束边界。
- 使用既有 `merge_clip_windows()` 合并重叠或接近的五杀片段。

2. 导出第二阶段五杀链函数。

修改文件：

```text
pentaforge/src/detector/__init__.py
```

新增导出：

```text
events_to_penta_clip_configs
```

3. 在检测结果中保留视频时长。

修改文件：

```text
pentaforge/src/detector/detect_pipeline.py
```

`DetectionResult` 新增字段：

```text
duration
```

用途：

- 让 `/api/detector/video` 返回视频时长。
- 让 `/api/detector/penta-export` 使用真实视频时长裁剪五杀片段边界。

4. 新增一键五杀导出接口。

修改文件：

```text
pentaforge/src/server.py
```

新增接口：

```text
POST /api/detector/penta-export
```

处理流程：

```text
detect_candidates_from_video()
  -> events_to_penta_clip_configs()
  -> _config_from_dict()
  -> _start_pipeline_job()
```

返回行为：

- 识别到五杀链时返回 `job_id`、`observations`、`events`、`clips`、`duration`。
- 未识别到五杀链时返回 `job_id: null`，并且不启动导出任务。
- OCR 依赖未安装时继续返回 501 清晰错误。
- 源视频缺失时继续返回 404。

5. 抽取 pipeline job 启动 helper。

修改文件：

```text
pentaforge/src/server.py
```

新增内部函数：

```text
_start_pipeline_job()
```

用途：

- 让 `/api/pipeline/run` 和 `/api/detector/penta-export` 复用同一套后台导出任务逻辑。
- 第一阶段 `run_pipeline_with_progress()` 未被改动，只被复用。

6. 新增前端一键五杀导出入口。

修改文件：

```text
pentaforge/web/src/api/client.js
pentaforge/web/src/components/DetectionPanel.vue
pentaforge/web/src/App.vue
```

新增能力：

- `client.js` 新增 `exportPentaKill()`。
- `DetectionPanel.vue` 新增“一键识别五杀并导出”按钮。
- 前端请求会带上 OCR 参数、五杀链参数、当前输出路径、音频设置、导出设置。
- 拿到 `job_id` 后复用现有 WebSocket 进度流。
- `App.vue` 接收检测面板事件并打开现有进度弹窗。
- 原有“从当前视频自动识别”和“添加全部到手动片段”保留。

### 已完成测试改动

修改文件：

```text
pentaforge/tests/test_detector_event_parser.py
pentaforge/tests/test_detector_boundary.py
```

新增/补充覆盖：

- `Double Kill` -> `double_kill`
- `Pentakill` -> `penta_kill`
- `Penta Kill` -> `penta_kill`
- `双杀`、`三杀`、`四杀`、`五杀`
- `雙殺`、`五殺`
- 双杀到五杀链生成 `115.0s -> 147.0s`
- 没有双杀但有五杀时，从链内最早事件前推
- 没有五杀的链不生成片段
- `chain_gap` 分链行为
- `video_duration` 边界裁剪
- 相近五杀片段合并

### 验证结果

已通过：

```powershell
$env:PYTHONPATH = (Resolve-Path -LiteralPath .\pentaforge).Path
.\.venv\Scripts\python.exe -m pytest .\pentaforge\tests\test_detector_event_parser.py .\pentaforge\tests\test_detector_boundary.py .\pentaforge\tests\test_detector_paddleocr_reader.py -q -p no:cacheprovider
```

结果：

```text
16 passed
```

已通过手动 fake reader 链路检查：

```text
manual detect pipeline check passed
```

该检查覆盖：

- 抽帧时间戳 `[0.0, 1.0]`
- fake OCR observation
- `triple_kill` 事件解析
- 候选片段 `0.5s -> 1.5s`
- `DetectionResult.duration == 2.0`

已通过 Python AST 语法检查：

```text
python syntax check passed
```

已通过前端生产构建：

```powershell
npm run build
```

结果：

```text
vite build completed
```

### 验证注意事项

完整 pytest 中 `test_detector_detect_pipeline.py` 使用 `tmp_path` fixture。当前沙箱对 pytest 默认临时目录和 `--basetemp` 目录的清理存在权限限制，会出现 `PermissionError: [WinError 5] 拒绝访问`。

因此本次采用：

- 不依赖 `tmp_path` 的 pytest 子集验证核心解析和边界逻辑。
- 手动 fake reader 脚本验证视频检测链路。
- 前端构建使用提权运行，因为 Vite/esbuild 在沙箱中启动子进程会触发 `spawn EPERM`。

### 后续建议

1. 用真实英雄联盟录屏短样本调用 `/api/detector/video`，先确认 `observations` 是否稳定出现击杀播报文本。
2. 如果 `observations` 为空，优先调 ROI 和采样间隔。
3. 如果 `observations` 有文本但 `events` 为空，继续扩展 `event_parser.py` 的 OCR 容错正则。
4. 如果五杀链片段过长或过短，微调 `pre_double_roll`、`post_penta_roll`、`chain_gap`。
5. 在确认真实样本稳定后，再补 `/api/detector/penta-export` 的 API 级测试。
