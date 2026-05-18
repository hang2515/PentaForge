<template>
  <section class="detection-panel">
    <div class="panel-header">
      <h3>自动识别候选</h3>
      <span>{{ candidates.length }} 个候选片段</span>
    </div>

    <div class="controls">
      <label>采样间隔 (秒)
        <input type="number" step="0.1" min="0.1" v-model.number="interval" />
      </label>
      <label>最多帧数
        <input type="number" step="1" min="1" v-model.number="maxFrames" />
      </label>
      <label>回溯 (秒)
        <input type="number" step="0.5" min="0" v-model.number="preRoll" />
      </label>
      <label>前瞻 (秒)
        <input type="number" step="0.5" min="0" v-model.number="postRoll" />
      </label>
      <label>合并间隔 (秒)
        <input type="number" step="0.5" min="0" v-model.number="mergeGap" />
      </label>
      <label>最小置信度
        <input type="number" step="0.05" min="0" max="1" v-model.number="minConfidence" />
      </label>
    </div>

    <div class="roi-controls">
      <label>ROI X
        <input type="number" step="0.01" min="0" max="1" v-model.number="roi.x" />
      </label>
      <label>ROI Y
        <input type="number" step="0.01" min="0" max="1" v-model.number="roi.y" />
      </label>
      <label>ROI 宽
        <input type="number" step="0.01" min="0.01" max="1" v-model.number="roi.width" />
      </label>
      <label>ROI 高
        <input type="number" step="0.01" min="0.01" max="1" v-model.number="roi.height" />
      </label>
    </div>

    <textarea
      v-model="observationsText"
      spellcheck="false"
      placeholder='粘贴识别文本，例如：[{"time":"1:30","text":"Triple Kill","confidence":0.92}]'
    />

    <div v-if="error" class="error">{{ error }}</div>

    <div class="actions">
      <button class="btn primary" @click="detectFromVideo" :disabled="loading || !store.source">
        {{ loading ? '识别中...' : '从当前视频自动识别' }}
      </button>
      <button class="btn" @click="generateCandidates" :disabled="loading">
        {{ loading ? '生成中...' : '生成候选片段' }}
      </button>
      <button class="btn" @click="addAllCandidates" :disabled="!candidates.length">
        添加全部到手动片段
      </button>
    </div>

    <div v-if="events.length" class="events">
      <div v-for="event in events" :key="`${event.time}-${event.kill_type}`" class="event-row">
        <span>{{ formatTime(event.time) }}</span>
        <strong>{{ event.kill_type }}</strong>
        <em>{{ event.text }}</em>
      </div>
    </div>

    <div v-if="candidates.length" class="candidate-list">
      <div v-for="(clip, index) in candidates" :key="`${clip.start}-${clip.end}-${index}`" class="candidate-card">
        <div>
          <strong>{{ clip.label || `候选 ${index + 1}` }}</strong>
          <span>{{ formatTime(clip.start) }} - {{ formatTime(clip.end) }}</span>
        </div>
        <button class="btn" @click="addCandidate(clip)">添加</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { useConfigStore } from '../stores/config.js'
import * as api from '../api/client.js'

const store = useConfigStore()
const interval = ref(0.5)
const maxFrames = ref(120)
const preRoll = ref(8)
const postRoll = ref(4)
const mergeGap = ref(2)
const minConfidence = ref(0.3)
const roi = ref({ x: 0.2, y: 0.06, width: 0.6, height: 0.24 })
const loading = ref(false)
const error = ref('')
const events = ref([])
const candidates = ref([])
const observationsText = ref(JSON.stringify([
  { time: '1:30', text: 'Triple Kill', confidence: 0.9 },
  { time: '5:20', text: 'Penta Kill', confidence: 0.95 },
], null, 2))

async function generateCandidates() {
  error.value = ''
  loading.value = true
  try {
    const observations = JSON.parse(observationsText.value)
    const result = await api.detectCandidateClips({
      observations,
      pre_roll: preRoll.value,
      post_roll: postRoll.value,
      merge_gap: mergeGap.value,
      video_duration: store.videoInfo?.duration ?? null,
    })
    events.value = result.events || []
    candidates.value = result.clips || []
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function detectFromVideo() {
  error.value = ''
  if (!store.source) {
    error.value = '请先选择源视频'
    return
  }
  loading.value = true
  try {
    const result = await api.detectVideoClips({
      source: store.source,
      interval: interval.value,
      max_frames: maxFrames.value || null,
      roi: roi.value,
      pre_roll: preRoll.value,
      post_roll: postRoll.value,
      merge_gap: mergeGap.value,
      min_confidence: minConfidence.value,
    })
    observationsText.value = JSON.stringify(result.observations || [], null, 2)
    events.value = result.events || []
    candidates.value = result.clips || []
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function addCandidate(clip) {
  store.clips = [...store.clips, normalizeClip(clip)]
}

function addAllCandidates() {
  store.clips = [...store.clips, ...candidates.value.map(normalizeClip)]
}

function normalizeClip(clip) {
  return {
    start: clip.start,
    end: clip.end,
    kill_type: clip.kill_type || '',
    label: clip.label || '',
    sfx_offset: clip.sfx_offset ?? null,
    bgm: clip.bgm || '',
    transition_after: clip.transition_after || null,
  }
}

function formatTime(value) {
  const seconds = Number(value || 0)
  const minutes = Math.floor(seconds / 60)
  const rest = (seconds % 60).toFixed(1).padStart(4, '0')
  return `${minutes}:${rest}`
}
</script>

<style scoped>
.detection-panel {
  background: #fff;
  border: 1px solid #e8d5c4;
  border-radius: 6px;
  padding: 10px;
}
.panel-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8px;
}
h3 {
  margin: 0;
  font-size: 14px;
  color: #5c3d2e;
}
.panel-header span {
  font-size: 11px;
  color: #8d6e63;
}
.controls {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  margin-bottom: 8px;
}
.roi-controls {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-bottom: 8px;
}
label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: #8d6e63;
  font-size: 11px;
}
input,
textarea {
  background: #fef9f4;
  border: 1px solid #d4b896;
  color: #4a3728;
  border-radius: 4px;
  font-size: 12px;
}
input {
  padding: 4px 6px;
}
textarea {
  width: 100%;
  min-height: 110px;
  padding: 8px;
  resize: vertical;
  font-family: Consolas, monospace;
}
.actions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.primary {
  background: #e07b3c;
  border-color: #e07b3c;
  color: #fff;
}
.primary:hover { background: #c96a2e; }
.error {
  margin-top: 6px;
  color: #c0392b;
  font-size: 12px;
}
.events,
.candidate-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.event-row,
.candidate-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 8px;
  background: #fef9f4;
  border: 1px solid #ead8c8;
  border-radius: 4px;
  font-size: 12px;
}
.event-row em {
  color: #8d6e63;
  font-style: normal;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.candidate-card div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.candidate-card span {
  color: #8d6e63;
  font-size: 11px;
}
</style>
