# PentaForge — 问题诊断与解决方案

> 2026-05-23

---

## 问题 1+5：多视频时间戳标记交互混乱 / 导入新视频后旧视频消失

### 根因

系统只支持 **单个** 源视频。`PipelineConfig.source` ([config_parser.py:42](pentaforge/src/config_parser.py#L42)) 和 `store.source` ([config.js:30](pentaforge/web/src/stores/config.js#L30)) 都是字符串，不是列表。

- 选择新视频 → 旧视频路径被覆盖
- Clip 没有任何字段关联到具体源视频
- Timeline 展示在一根时间轴上，但无法区分不同视频的片段

### 解决方案（已修复）

**前端**：
- `config.js`: `sources: []` 数组 + `activeSourceIndex`，每 source 独立存储 `_clips`
- `VideoPanel.vue`: 横向视频卡片列表，支持多视频添加/删除/切换
- `TimelineScrubber.vue`: 显示当前选中视频的片段
- `PipelineRunner.vue`: 发送 `sources` 数组 + 每个 clip 的 `source_index`

**后端**：
- `config_parser.py`: 新增 `SourceConfig` 数据类，`PipelineConfig` 新增 `sources: list[SourceConfig]`，`ClipConfig` 新增 `source_index: int`
- `PipelineConfig.source_for(clip)` 方法：根据 clip 的 `source_index` 解析对应源文件路径，兼容旧单文件格式
- `server.py`: `_config_from_dict()` 处理 `sources` 数组 + `source_index`
- `pipeline.py`: `run_pipeline()` 和 `run_pipeline_with_progress()` 均使用 `config.source_for(clip)` 获取源路径

**影响范围**：`config_parser.py`、`server.py`、`pipeline.py`、`config.js`、`VideoPanel.vue`、`TimelineScrubber.vue`、`PipelineRunner.vue`

---

## 问题 2：视频完全没声音

### 根因（两个 Bug）

**Bug A** — `clip_extractor.py:28`：音频流未被映射到输出

```python
# line 24-28
stream = ffmpeg.input(source, ss=start, t=duration)
# ...
stream = ffmpeg.output(stream.video, output, **out_kwargs)  # ← stream.video 只选了视频流！
```

`stream.video` 只选择了视频流，即使没加 `an` 参数，音频也从未被映射到输出文件。

**Bug B** — `pipeline.py:53-57`：`audio_enabled=True` + 无 BGM → 静音

当用户勾选"启用音频混音"但未配置 BGM 文件时：
- `keep_audio = not config.audio_enabled` = `False` → 音频被 strip
- `config.audio_enabled and bgm` = `False`（bgm 为空字符串）→ 混音步骤被跳过
- 结果：视频无音频轨道

### 解决方案（已修复）

**修复 Bug A**：显式映射 audio 流

```python
inp = ffmpeg.input(source, ss=start, t=duration)
if keep_audio:
    stream = ffmpeg.output(inp.video, inp.audio, output, **out_kwargs)
else:
    stream = ffmpeg.output(inp.video, output, an=None, **out_kwargs)
```

**修复 Bug B**：使用 `has_audio_mix` 标志，区分"保留原声"和"替换为混音"

```python
has_audio_mix = config.audio_enabled and bool(bgm)
keep_audio = not has_audio_mix
extract_video(..., keep_audio=keep_audio)
```

**影响范围**：`clip_extractor.py`、`pipeline.py`

---

## 问题 3：没有按时间戳标记剪辑，只剪前几秒并重复拼接

### 根因

`emptyClip()` 返回 `{start: 0, end: 5}` — 所有新建 clip 都默认 0~5 秒：

```javascript
// config.js:24-26 (old)
function emptyClip() {
  return { start: 0, end: 5, kill_type: '', label: '', sfx_offset: null, bgm: '' }
}
```

因为问题 1 的交互太差，用户无法正确标记时间戳，实际提交的 clip 时间就是默认值。2 个 clip（初始 + "添加片段"）都是 0~5s，拼接后就是"前 5 秒重复两遍"。

### 解决方案（已修复）

1. **问题 1+5 已修复** — 多视频管理 + Timeline 拖拽交互改善，时间戳标记不再混乱
2. **`emptyClip()` 优化** — 根据视频时长自动设置默认片段位置（取视频中间段），而非硬编码 0~5s：

```javascript
function emptyClip(sourceIdx = 0, videoDuration = 0) {
  const dur = Math.min(5, videoDuration > 0 ? videoDuration / 6 : 5)
  const start = videoDuration > 0 ? Math.max(0, (videoDuration - dur) / 2) : 0
  return { start, end: start + dur, ... }
}
```

3. **问题 8 已修复** — 两端手柄均可独立拖拽，时间戳可精确调整

**影响范围**：`config.js`、`TimelineScrubber.vue`

---

## 问题 4：进度条只停留在一半

### 根因

`pipeline.py:116`：`total_steps` 硬编码为 `total_clips * 3 + 1`，但每个 clip 实际执行步骤取决于 `audio_enabled` 和是否有 BGM。

另外 `start.bat` 未加 `--reload` 参数，代码修改后需手动重启后端。

### 解决方案（已修复）

1. `total_steps` 现在根据实际步骤数动态计算：遍历所有 clips，对每个 clip 根据 `audio_enabled && bgm` 判断是 1 步还是 3 步
2. `start.bat` 已添加 `--reload` 以便开发时自动重载

**影响范围**：`pipeline.py`、`start.bat`

---

## 问题 6：完全看不出转场效果

### 根因

1. **默认转场时间太短**：`transition_dur = 0.3s`，0.3 秒 fade 几乎不可见
2. **只有两个相同片段拼接**（问题 3）：0~5s 的片段拼接到 0~5s 的片段，内容完全相同，即使有转场也看不出来

### 解决方案（已修复）

1. 默认转场时间从 `0.3s` 改为 `0.6s`（`config_parser.py` 和 `config.js` 均已更新）
2. 问题 3 修复后片段内容不同，转场自然会显现

**影响范围**：`config_parser.py`、`config.js`

---

## 问题 7：UI 设计实在太烂

### 解决方案（已完成）

使用 `frontend-design` skill 对整个前端进行全面重构。Hextech 暗色主题 → 亮色现代主题。
所有组件已重写：`VideoPanel`、`VideoPreview`、`TimelineScrubber`、`ClipEditor`、`ConfigForm`、`AudioSettings`、`TransitionSettings`、`ExportSettings`、`ProgressOverlay`、`PipelineRunner`。

---

## 问题 8：时间轴只能拖动一侧手柄，另一侧固定不动

### 根因

**Bug A** — 手柄渲染/命中检测在画布外不可见

当 clip 超出画布可见区域时，手柄渲染在 canvas 边界之外，点击命中检测也使用未裁剪的坐标。特别影响 end 手柄：clip 结束时间在可见范围右侧时，右手柄从画布右侧消失。

**Bug B** — 手柄命中区域太小

`HANDLE_W = 10`，命中容差 `HANDLE_W + 2 = 12px`。高 DPI 或缩小时容易误点到 clip body。

### 解决方案（已修复）

1. **手柄绘制坐标裁剪**：handle 绘制位置限制在 `[PADDING_X, PADDING_X + layoutW()]` 范围内（[TimelineScrubber.vue:195](pentaforge/web/src/components/TimelineScrubber.vue#L195)）
2. **命中检测坐标裁剪**：hitTest 中 x1/x2 同样限制在可见范围内（[TimelineScrubber.vue:283-284](pentaforge/web/src/components/TimelineScrubber.vue#L283-L284)）
3. **命中容差增大**：从 12px 增加到 16px（`HANDLE_HIT_TOLERANCE = 6`）
4. **Hover 视觉反馈**：手柄 hover 时显示边框高亮

**影响范围**：`TimelineScrubber.vue`

---

## 修复状态总览

| 优先级 | 问题 | 状态 |
|--------|------|------|
| P0 | 问题 2（无声音） | ✅ 已修复 |
| P0 | 问题 3（剪辑错误） | ✅ 已修复（借助问题 1+8） |
| P1 | 问题 1+5（多视频/交互） | ✅ 已修复（前后端均支持） |
| P1 | 问题 4（进度条） | ✅ 已修复 |
| P1 | 问题 8（手柄拖拽） | ✅ 已修复 |
| P2 | 问题 6（转场） | ✅ 已修复 |
| P3 | 问题 7（UI 重构） | ✅ 已完成 |
