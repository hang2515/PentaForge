<template>
  <div class="pipeline-runner">
    <button
      class="run-btn"
      :class="{ running: running, ready: ready }"
      :disabled="!ready || running"
      @click="run"
    >
      <span v-if="running" class="spinner" />
      <svg v-else viewBox="0 0 16 16" width="14" height="14" class="forge-icon">
        <polygon points="8,1 14,5 14,11 8,15 2,11 2,5" fill="none" stroke="currentColor" stroke-width="1.2"/>
        <circle cx="8" cy="8" r="2" fill="currentColor"/>
      </svg>
      {{ running ? '处理中...' : '开始剪辑' }}
    </button>
    <span v-if="statusText" class="status" :class="statusType">{{ statusText }}</span>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useConfigStore } from '../stores/config.js'
import * as api from '../api/client.js'

const store = useConfigStore()
const running = ref(false)
const status = ref('')

const emit = defineEmits(['start', 'message'])

const ready = computed(() => {
  return store.sources.length > 0 && store.allClips.length > 0
})

const statusText = computed(() => {
  const map = {
    starting: '启动中...', running: '处理中...', completed: '完成',
    error: '出错', disconnected: '连接断开', 'connection error': '连接错误',
  }
  return map[status.value] || ''
})

const statusType = computed(() => {
  if (status.value === 'completed') return 'done'
  if (status.value === 'error' || status.value === 'connection error') return 'error'
  return 'running'
})

async function run() {
  running.value = true
  status.value = 'starting'
  store.pipelineMessages = []
  store.activeJobId = null

  const allClips = store.allClips

  try {
    const { job_id } = await api.runPipeline({
      source: store.sources[0]?.path || '',
      sources: store.sources.map(s => ({ path: s.path, name: s.name })),
      output: store.output,
      bgm: store.bgm,
      bgm_volume: store.bgm_volume,
      sfx: store.sfx,
      sfx_volume: store.sfx_volume,
      audio_enabled: store.audio_enabled,
      transitions: store.transitions,
      export: store.export,
      clips: allClips.map(c => ({
        start: c.start,
        end: c.end,
        kill_type: c.kill_type || '',
        label: c.label || '',
        sfx_offset: c.sfx_offset ?? null,
        bgm: c.bgm || '',
        source_index: c.sourceIndex ?? 0,
      })),
      temp_dir: store.temp_dir,
    })
    store.activeJobId = job_id
    status.value = 'running'
    emit('start', job_id)

    const ws = api.connectProgress(job_id,
      (msg) => {
        store.addPipelineMessage(msg)
        emit('message', msg)
        if (msg.type === 'complete') {
          status.value = 'completed'
          running.value = false
          ws.close()
        } else if (msg.type === 'error') {
          status.value = 'error'
          running.value = false
          ws.close()
        }
      },
      () => {
        if (running.value) {
          status.value = 'disconnected'
          running.value = false
        }
      },
      (err) => {
        console.error('WS error:', err)
        status.value = 'connection error'
        running.value = false
      }
    )
  } catch (e) {
    status.value = 'error'
    running.value = false
    store.addPipelineMessage({ type: 'error', message: e.message })
  }
}
</script>

<style scoped>
.pipeline-runner {
  display: flex;
  align-items: center;
  gap: 12px;
}
.run-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 22px;
  background: var(--gold);
  border: 1px solid var(--gold);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  font-family: var(--font-display);
  letter-spacing: 0.06em;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition);
  text-transform: uppercase;
}
.run-btn:hover:not(:disabled) {
  background: var(--gold-light);
  border-color: var(--gold-light);
  box-shadow: 0 2px 12px rgba(184, 134, 11, 0.3);
}
.run-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.run-btn.running {
  animation: pulse 1.5s ease-in-out infinite;
}
.forge-icon {
  opacity: 0.9;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(184, 134, 11, 0.15); }
  50% { box-shadow: 0 0 0 6px rgba(184, 134, 11, 0.08); }
}

.spinner {
  width: 14px; height: 14px;
  border: 2px solid var(--gold-dim);
  border-top-color: var(--gold);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.status {
  font-size: 12px;
  font-family: var(--font-mono);
}
.status.running { color: var(--gold); }
.status.done { color: var(--accent-green); }
.status.error { color: var(--accent-red); }
</style>
