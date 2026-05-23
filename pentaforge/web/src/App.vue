<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="logo">
        <svg class="logo-icon" viewBox="0 0 32 32" width="28" height="28">
          <polygon points="16,2 26,10 26,22 16,30 6,22 6,10" fill="none" stroke="var(--gold)" stroke-width="1.5"/>
          <polygon points="16,6 23,12 23,20 16,26 9,20 9,12" fill="none" stroke="var(--gold-light)" stroke-width="1"/>
          <circle cx="16" cy="16" r="3" fill="var(--gold)"/>
        </svg>
        <span class="logo-text">PentaForge</span>
      </div>
      <span class="subtitle">Highlight Configurator</span>
      <div class="header-actions">
        <PipelineRunner @start="showProgress = true" @message="onPipelineMessage" />
      </div>
    </header>

    <main class="main-layout">
      <!-- Left sidebar: sources + settings -->
      <aside class="sidebar">
        <VideoPanel />
        <div class="settings-scroll">
          <ConfigForm />
        </div>
      </aside>

      <!-- Center: preview + timeline (left) + clip editor (right) -->
      <section class="workspace">
        <div class="workspace-left">
          <VideoPreview ref="videoRef" @update:current-time="currentTime = $event" />
          <TimelineScrubber
            :videoDuration="store.videoDuration"
            :clips="store.activeClips"
            :currentTime="currentTime"
            :colors="store.clipColors"
            @update:clips="clips => store.setAllClips(store.activeSourceIndex, clips)"
            @seek="seekVideo"
          />
        </div>
        <div class="workspace-right">
          <ClipEditor
            :clips="store.activeClips"
            :sourceIndex="store.activeSourceIndex"
            :colors="store.clipColors"
            @update:clips="clips => store.setAllClips(store.activeSourceIndex, clips)"
            @add-clip="store.addClip(store.activeSourceIndex)"
            @remove-clip="(ci) => store.removeClip(store.activeSourceIndex, ci)"
          />
        </div>
      </section>
    </main>

    <ProgressOverlay :visible="showProgress" @close="showProgress = false" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useConfigStore } from './stores/config.js'
import VideoPanel from './components/VideoPanel.vue'
import VideoPreview from './components/VideoPreview.vue'
import TimelineScrubber from './components/TimelineScrubber.vue'
import ClipEditor from './components/ClipEditor.vue'
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

function onPipelineMessage(msg) {
  if (msg.type === 'complete' || msg.type === 'error') {
    // keep overlay open to show result
  }
}
</script>

<style>
/* ── Light Design System ── */
:root {
  --bg-deep: #f0f2f5;
  --bg-surface: #ffffff;
  --bg-elevated: #f8f9fb;
  --bg-input: #f0f2f5;
  --border: #dde1e6;
  --border-accent: #c8cdd5;
  --gold: #b8860b;
  --gold-dim: #9a7000;
  --gold-light: #8b6914;
  --gold-glow: rgba(184, 134, 11, 0.12);
  --text-primary: #1a1d2e;
  --text-secondary: #6b7280;
  --text-muted: #9ca3af;
  --accent-blue: #3b82f6;
  --accent-red: #ef4444;
  --accent-green: #22c55e;
  --accent-orange: #f97316;
  --font-display: 'Cinzel', serif;
  --font-body: 'Noto Sans SC', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --radius: 4px;
  --radius-lg: 8px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  --shadow-gold: 0 0 0 3px rgba(184, 134, 11, 0.1);
  --transition: 0.2s ease;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: var(--font-body);
  background: var(--bg-deep);
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.5;
  overflow: hidden;
  height: 100vh;
}

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--border-accent); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

button, input, select, textarea {
  font-family: inherit;
  font-size: inherit;
}

input, select, textarea {
  background: var(--bg-input);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 6px 10px;
  border-radius: var(--radius);
  transition: border-color var(--transition), box-shadow var(--transition);
}
input:focus, select:focus, textarea:focus {
  outline: none;
  border-color: var(--gold);
  box-shadow: 0 0 0 3px rgba(184, 134, 11, 0.1);
}
input::placeholder { color: var(--text-muted); }

.btn {
  padding: 6px 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all var(--transition);
  box-shadow: var(--shadow-sm);
}
.btn:hover {
  border-color: var(--gold);
  color: var(--gold-light);
  box-shadow: var(--shadow-md);
}

.btn-primary {
  background: var(--gold);
  border-color: var(--gold);
  color: #fff;
  font-weight: 600;
}
.btn-primary:hover {
  background: var(--gold-light);
  border-color: var(--gold-light);
  color: #fff;
  box-shadow: var(--shadow-md);
}

.btn-icon {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius);
  transition: color var(--transition);
  line-height: 1;
}
.btn-icon:hover { color: var(--accent-red); }

.section-title {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}

label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

input[type="range"] {
  -webkit-appearance: none;
  background: transparent;
  border: none;
  padding: 0;
  height: 4px;
}
input[type="range"]::-webkit-slider-runnable-track {
  background: var(--border);
  height: 4px;
  border-radius: 2px;
}
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px; height: 14px;
  background: var(--gold);
  border-radius: 50%;
  margin-top: -5px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
}
input[type="checkbox"] {
  accent-color: var(--gold);
  width: 16px; height: 16px;
}
</style>

<style scoped>
.app-shell {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-deep);
}

.app-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 20px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  flex-shrink: 0;
  z-index: 10;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo svg polygon, .logo svg circle { stroke: var(--gold); }
.logo svg circle { fill: var(--gold); }
.logo-text {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--gold);
  letter-spacing: 0.06em;
}
.subtitle {
  color: var(--text-muted);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.header-actions { margin-left: auto; }

.main-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  flex: 1;
  overflow: hidden;
  height: 0;
}

.sidebar {
  background: var(--bg-surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.settings-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
}

.workspace {
  display: flex;
  gap: 12px;
  overflow-y: auto;
  padding: 16px;
}
.workspace-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}
.workspace-right {
  width: 320px;
  flex-shrink: 0;
  overflow-y: auto;
}
</style>
