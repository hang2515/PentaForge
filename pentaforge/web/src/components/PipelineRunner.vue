<template>
  <div class="pipeline-runner">
    <button class="btn-run" :disabled="!ready || running" @click="run">
      {{ running ? '处理中...' : '开始剪辑' }}
    </button>
    <span v-if="status" class="status" :class="statusType">{{ statusText }}</span>
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

const ready = computed(() => store.source && store.clips.length > 0)

const statusText = computed(() => {
  const map = { starting: '启动中...', running: '处理中...', completed: '完成', error: '出错', disconnected: '连接断开', 'connection error': '连接错误' }
  return map[status.value] || status.value
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

  try {
    const { job_id } = await api.runPipeline({
      source: store.source,
      output: store.output,
      bgm: store.bgm,
      bgm_volume: store.bgmVolume,
      sfx: store.sfx,
      sfx_volume: store.sfxVolume,
      transitions: store.transitions,
      export: store.export,
      clips: store.clips,
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
.btn-run {
  padding: 8px 24px;
  background: #e07b3c;
  border: none;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
}
.btn-run:hover { background: #c96a2e; }
.btn-run:disabled {
  background: #d4b896;
  color: #f5ede3;
  cursor: not-allowed;
}
.status { font-size: 13px; }
.status.running { color: #d4742b; }
.status.done { color: #8b9a46; }
.status.error { color: #c0392b; }
</style>
