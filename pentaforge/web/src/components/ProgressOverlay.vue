<template>
  <Transition name="modal">
    <div v-if="visible" class="overlay" @click.self="handleClose">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ done ? (isError ? '处理失败' : '完成') : '正在剪辑...' }}</h3>
          <button class="btn-icon" @click="handleClose">&times;</button>
        </div>

        <div class="progress-section">
          <div class="progress-bar">
            <div class="fill" :class="{ done: done && !isError, error: isError }" :style="{ width: percent + '%' }">
              <div class="fill-glow" />
            </div>
          </div>
          <div class="progress-text">
            <span>{{ percent }}%</span>
            <span class="step-label">{{ currentStepText }}</span>
          </div>
        </div>

        <div class="msg-log" ref="logEl">
          <div v-for="(msg, i) in store.pipelineMessages" :key="i" class="log-line" :class="msg.type">
            <span class="log-dot" :class="msg.type" />
            {{ msg.message || msg.type }}
          </div>
        </div>

        <div v-if="lastResult && done" class="result-info">
          <div v-if="lastResult.output_path" class="output-path">
            <span class="result-label">输出文件</span>
            <code>{{ lastResult.output_path }}</code>
          </div>
          <div v-if="lastResult.errors?.length" class="error-list">
            <span class="result-label error">错误</span>
            <code v-for="(e, i) in lastResult.errors" :key="i">{{ e }}</code>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { useConfigStore } from '../stores/config.js'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['close'])

const store = useConfigStore()
const logEl = ref(null)
const currentStepText = ref('正在连接...')

const steps = computed(() => store.pipelineMessages.filter(m => m.type === 'step'))
const lastStep = computed(() => steps.value[steps.value.length - 1])

const lastResult = computed(() => {
  return store.pipelineMessages.find(m => m.type === 'complete' || m.type === 'error') || null
})

const isError = computed(() => {
  return lastResult.value?.type === 'error'
})

watch(lastStep, (s) => {
  if (s) {
    currentStepText.value = s.message
    nextTick(() => {
      if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
    })
  }
})

const percent = computed(() => {
  const steps_arr = steps.value
  if (steps_arr.length === 0) return 0
  const last = steps_arr[steps_arr.length - 1]
  if (!last || !last.total) return 0
  return Math.min(100, Math.round((last.step / last.total) * 100))
})

const done = computed(() => {
  const msgs = store.pipelineMessages
  if (msgs.length === 0) return false
  const last = msgs[msgs.length - 1]
  return last && (last.type === 'complete' || last.type === 'error')
})

function handleClose() {
  if (done.value) {
    store.pipelineMessages = []
    emit('close')
  }
}
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.modal {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  width: 480px;
  max-width: 92vw;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.modal-header h3 {
  font-family: var(--font-display);
  font-size: 16px;
  color: var(--gold);
  font-weight: 600;
}

.progress-section { margin-bottom: 14px; }
.progress-bar {
  height: 6px;
  background: var(--bg-deep);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 6px;
}
.fill {
  height: 100%;
  background: linear-gradient(90deg, var(--gold-dim), var(--gold));
  border-radius: 3px;
  transition: width 0.4s ease;
  position: relative;
}
.fill.done { background: linear-gradient(90deg, #3a8a6a, #5eaa8e); }
.fill.error { background: linear-gradient(90deg, #8a3030, #e06050); }
.fill-glow {
  position: absolute;
  right: 0; top: 0; bottom: 0;
  width: 20px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3));
}
.progress-text {
  display: flex;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
}
.step-label {
  color: var(--text-muted);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.msg-log {
  max-height: 180px;
  overflow-y: auto;
  margin-bottom: 12px;
  background: var(--bg-deep);
  border-radius: var(--radius);
  padding: 8px 10px;
}
.log-line {
  font-size: 11px;
  color: var(--text-muted);
  padding: 2px 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
}
.log-line.step { color: var(--text-secondary); }
.log-line.complete { color: var(--accent-green); }
.log-line.error { color: var(--accent-red); }
.log-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
}
.log-dot.step { background: var(--gold); }
.log-dot.complete { background: var(--accent-green); }
.log-dot.error { background: var(--accent-red); }

.result-info {
  background: var(--bg-deep);
  border-radius: var(--radius);
  padding: 10px;
}
.result-label {
  font-family: var(--font-display);
  font-size: 10px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  display: block;
  margin-bottom: 4px;
}
.result-label.error { color: var(--accent-red); }
.output-path code, .error-list code {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-primary);
  word-break: break-all;
  display: block;
  margin-bottom: 2px;
}

/* Transition */
.modal-enter-active { transition: all 0.3s ease; }
.modal-leave-active { transition: all 0.2s ease; }
.modal-enter-from { opacity: 0; transform: scale(0.95); }
.modal-leave-to { opacity: 0; transform: scale(0.95); }
</style>
