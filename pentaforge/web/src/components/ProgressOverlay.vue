<template>
  <div v-if="visible" class="overlay" @click.self="$emit('close')">
    <div class="modal">
      <h3>剪辑进度</h3>
      <div class="progress-bar">
        <div class="fill" :style="{ width: percent + '%' }" />
      </div>
      <div class="step-info">{{ currentStepText }}</div>
      <div class="msg-log" ref="logEl">
        <div v-for="(msg, i) in store.pipelineMessages" :key="i" class="log-line" :class="msg.type">
          <span class="dot" :class="msg.type" />
          {{ msg.message || msg.type }}
        </div>
      </div>
      <div v-if="done" class="result">
        <div v-if="lastComplete?.output_path" class="output-path">
          输出: {{ lastComplete.output_path }}
        </div>
        <div v-if="lastComplete?.errors?.length" class="errors">
          错误: {{ lastComplete.errors.join(', ') }}
        </div>
      </div>
      <button class="btn" @click="$emit('close')">{{ done ? '关闭' : '取消' }}</button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { useConfigStore } from '../stores/config.js'

const props = defineProps({ visible: Boolean })
defineEmits(['close'])

const store = useConfigStore()
const logEl = ref(null)
const currentStepText = ref('')

const lastComplete = computed(() => {
  return store.pipelineMessages.find(m => m.type === 'complete' || m.type === 'error') || null
})

const steps = computed(() => store.pipelineMessages.filter(m => m.type === 'step'))
const lastStep = computed(() => steps.value[steps.value.length - 1])

watch(lastStep, (s) => {
  if (s) {
    currentStepText.value = s.message
    nextTick(() => {
      if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
    })
  }
})

const percent = computed(() => {
  const last = steps.value[steps.value.length - 1]
  if (!last) return 0
  return Math.round((last.step / last.total) * 100)
})

const done = computed(() => {
  const last = store.pipelineMessages[store.pipelineMessages.length - 1]
  return last && (last.type === 'complete' || last.type === 'error')
})
</script>

<style scoped>
.overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(74, 55, 40, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal {
  background: #fff;
  border: 1px solid #e8d5c4;
  border-radius: 10px;
  padding: 24px;
  width: 480px;
  max-width: 90vw;
  box-shadow: 0 8px 32px rgba(74, 55, 40, 0.15);
}
h3 { margin: 0 0 12px; color: #5c3d2e; }
.progress-bar {
  height: 8px;
  background: #f5ede3;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}
.fill {
  height: 100%;
  background: #e07b3c;
  transition: width 0.3s;
}
.step-info { font-size: 13px; color: #8d6e63; margin-bottom: 8px; min-height: 18px; }
.msg-log {
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 12px;
  font-size: 12px;
}
.log-line {
  padding: 3px 0;
  color: #8d6e63;
  display: flex;
  align-items: center;
  gap: 6px;
}
.dot {
  width: 6px; height: 6px; border-radius: 50%;
  display: inline-block;
}
.dot.step { background: #e07b3c; }
.dot.complete { background: #8b9a46; }
.dot.error { background: #c0392b; }
.log-line.error { color: #c0392b; }
.log-line.complete { color: #8b9a46; }
.result { font-size: 12px; color: #8b9a46; margin-bottom: 8px; }
.output-path { word-break: break-all; }
.errors { color: #c0392b; }
.btn {
  padding: 6px 20px;
  background: #f5ede3;
  border: 1px solid #d4b896;
  color: #5c3d2e;
  border-radius: 4px;
  cursor: pointer;
}
.btn:hover { background: #ede0d3; }
</style>
