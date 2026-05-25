# OCR 识别五杀并自动剪辑成片方案

## 目标

在 PentaForge 中新增“一键五杀成片”流程：

1. 输入《英雄联盟》录屏视频。
2. 使用 PaddleOCR 识别视频中的多杀文字。
3. 识别 `双杀`、`三杀`、`四杀`、`五杀`。
4. 当识别到同一段多杀链包含 `五杀` 时，自动生成剪辑片段。
5. 片段起点：从 `双杀` 出现时间往前推 15 秒。
6. 片段终点：到 `五杀` 出现时间后 3 秒。
7. 自动调用现有 FFmpeg 剪辑流水线导出完整视频。

## 核心流程

```text
录屏视频
  -> 按间隔抽帧
  -> 裁剪击杀播报 ROI 区域
  -> PaddleOCR 识别文字
  -> 解析双杀/三杀/四杀/五杀事件
  -> 找到包含五杀的多杀链
  -> 从双杀前 15 秒到五杀后 3 秒生成 clip
  -> 调用现有 pipeline 导出视频
```

## OCR 识别规则

需要支持以下文字：

| 类型 | 中文简体 | 中文繁体 | 英文 |
|---|---|---|---|
| 双杀 | 双杀 | 雙殺 | Double Kill |
| 三杀 | 三杀 | 三殺 | Triple Kill |
| 四杀 | 四杀 | 四殺 | Quadra Kill |
| 五杀 | 五杀 | 五殺 | Penta Kill / Pentakill |

当前项目中的中文正则存在乱码，应先修复为真实中文字符。

## 片段边界规则

默认规则：

```text
clip_start = double_kill_time - 15s
clip_end = penta_kill_time + 3s
```

如果同一条多杀链中没有识别到 `双杀`：

```text
clip_start = earliest_event_time - 15s
clip_end = penta_kill_time + 3s
```

边界需要裁剪到视频范围内：

```text
clip_start >= 0
clip_end <= video_duration
```

## 多杀链判断

按时间顺序排列 OCR 识别出的事件。

同一条多杀链默认规则：

- 相邻多杀事件间隔不超过 12 秒。
- 链内只要包含 `penta_kill`，就生成五杀剪辑片段。
- 片段主类型使用 `penta_kill`。
- 多个重叠或非常接近的五杀片段应合并。

示例：

```text
02:10 双杀
02:15 三杀
02:20 四杀
02:24 五杀
```

生成片段：

```text
start = 02:10 - 15s = 01:55
end = 02:24 + 3s = 02:27
```

## 后端改动

### 1. 修复事件解析

修改：

```text
pentaforge/src/detector/event_parser.py
```

确保 `detect_kill_type()` 能识别真实中文：

```text
双杀、三杀、四杀、五杀
雙殺、三殺、四殺、五殺
Double Kill、Triple Kill、Quadra Kill、Penta Kill、Pentakill
```

### 2. 新增五杀链边界算法

建议新增或扩展：

```text
pentaforge/src/detector/boundary.py
```

新增能力：

```text
events_to_penta_clip_configs(
    events,
    pre_double_roll=15.0,
    post_penta_roll=3.0,
    chain_gap=12.0,
    merge_gap=2.0,
    video_duration=None,
)
```

输出 `ClipConfig` 列表。

### 3. 新增一键导出接口

建议新增接口：

```text
POST /api/detector/penta-export
```

请求参数：

```json
{
  "source": "D:/videos/game.mp4",
  "roi": {
    "x": 0.2,
    "y": 0.06,
    "width": 0.6,
    "height": 0.24
  },
  "interval": 0.5,
  "min_confidence": 0.3,
  "max_frames": null,
  "pre_double_roll": 15,
  "post_penta_roll": 3,
  "chain_gap": 12,
  "output": "highlight_penta.mp4"
}
```

处理流程：

```text
detect_candidates_from_video()
  -> parse_kill_events()
  -> events_to_penta_clip_configs()
  -> PipelineConfig
  -> run_pipeline_with_progress()
```

返回：

```json
{
  "job_id": "xxxxxx",
  "clips": [
    {
      "start": 115.0,
      "end": 147.0,
      "kill_type": "penta_kill",
      "label": "Auto penta kill 1"
    }
  ]
}
```

进度继续复用现有接口：

```text
GET /api/pipeline/status/{job_id}
WS  /ws/progress/{job_id}
```

## 前端改动

修改：

```text
pentaforge/web/src/components/DetectionPanel.vue
```

新增按钮：

```text
一键识别五杀并导出
```

默认参数：

```text
采样间隔：0.5 秒
最低置信度：0.3
ROI：x=0.2, y=0.06, width=0.6, height=0.24
双杀前推：15 秒
五杀后留尾：3 秒
多杀链最大间隔：12 秒
```

交互：

1. 用户选择源视频。
2. 点击“一键识别五杀并导出”。
3. 页面显示 OCR 识别状态。
4. 识别到五杀后显示生成的片段。
5. 自动启动导出任务。
6. 导出完成后显示输出路径。

## 测试计划

### 单元测试

新增或更新：

```text
pentaforge/tests/test_detector_event_parser.py
pentaforge/tests/test_detector_boundary.py
```

测试点：

- `双杀` 能识别为 `double_kill`。
- `五杀` 能识别为 `penta_kill`。
- `Double Kill` 能识别为 `double_kill`。
- `Penta Kill` 能识别为 `penta_kill`。
- 双杀到五杀链生成正确片段。
- 默认起点为双杀前 15 秒。
- 默认终点为五杀后 3 秒。
- 视频边界能正确裁剪。
- 没有双杀但有五杀时，使用链内最早事件回退。

### API 测试

测试：

- 缺少 `source` 返回 400。
- OCR 依赖未安装时返回清晰提示。
- 未识别到五杀时不启动导出。
- 识别到五杀时返回 `job_id` 和 clips。
- 导出任务能通过现有进度接口查询。

## 默认策略

首版只使用 OCR，不做模板匹配或音频指纹。

默认剪辑规则固定为：

```text
双杀前 15 秒 -> 五杀后 3 秒
```

保留现有半自动候选功能。一键导出只是新增入口，不删除手动修正流程。
