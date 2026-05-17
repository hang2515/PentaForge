<template>
  <div class="app-shell">
    <header class="app-header">
      <h1>PentaForge</h1>
      <span class="subtitle">Highlight Configurator</span>
    </header>
    <main class="main-layout">
      <aside class="config-panel">
        <ConfigForm />
      </aside>
      <section class="preview-panel">
        <VideoPreview ref="videoRef" @update:current-time="currentTime = $event" />
        <TimelineScrubber
          :videoDuration="store.videoInfo?.duration || 0"
          :clips="store.clips"
          :currentTime="currentTime"
          @update:clips="store.clips = $event"
          @seek="seekVideo"
        />
        <PipelineRunner @start="onPipelineStart" @message="onPipelineMessage" />
      </section>
    </main>
    <ProgressOverlay :visible="showProgress" @close="showProgress = false" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useConfigStore } from './stores/config.js'
import VideoPreview from './components/VideoPreview.vue'
import TimelineScrubber from './components/TimelineScrubber.vue'
import ConfigForm from './components/ConfigForm.vue'
import PipelineRunner from './components/PipelineRunner.vue'
import ProgressOverlay from './components/ProgressOverlay.vue'

const store = useConfigStore()
const currentTime = ref(0)
const showProgress = ref(false)
const videoRef = ref(null)

function seekVideo(time) {
  if (videoRef.value) videoRef.value.seek(time)
}

function onPipelineStart() {
  showProgress.value = true
}

function onPipelineMessage(msg) {
  if (msg.type === 'complete' || msg.type === 'error') {
    // stay open for a moment to show result
  }
}
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #fef9f4;
  color: #4a3728;
  font-size: 14px;
}
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f5ede3; }
::-webkit-scrollbar-thumb { background: #c4a88c; border-radius: 3px; }

button, input, select, textarea { font-family: inherit; }
button.btn {
  padding: 6px 14px;
  background: #f5ede3;
  border: 1px solid #d4b896;
  color: #5c3d2e;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
button.btn:hover { background: #ede0d3; }
</style>

<style scoped>
.app-shell {
  max-width: 1280px;
  margin: 0 auto;
  padding: 16px;
  min-height: 100vh;
}
.app-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e8d5c4;
}
.app-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: #d4742b;
}
.subtitle { color: #b8a088; font-size: 13px; }
.main-layout {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 20px;
}
.config-panel {
  overflow-y: auto;
  max-height: calc(100vh - 120px);
}
.preview-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

@media (max-width: 900px) {
  .main-layout {
    grid-template-columns: 1fr;
  }
}
</style>
