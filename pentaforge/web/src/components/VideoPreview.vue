<template>
  <div class="video-preview" :class="{ 'has-video': store.sourcePath }">
    <div v-if="!store.sourcePath" class="placeholder">
      <svg viewBox="0 0 48 48" width="48" height="48">
        <rect x="4" y="8" width="40" height="32" rx="3" fill="none" stroke="var(--text-muted)" stroke-width="1"/>
        <polygon points="19,16 19,32 32,24" fill="var(--text-muted)"/>
      </svg>
      <p>添加视频素材开始标记高光片段</p>
    </div>
    <div v-show="store.sourcePath" class="video-container">
      <video
        ref="videoEl"
        :src="store.videoSrc"
        :poster="poster"
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onLoaded"
        @seeked="onSeeked"
        @play="paused = false"
        @pause="paused = true"
        preload="auto"
        controls
      />
      <button v-if="paused" class="play-overlay" @click="togglePlay">
        <svg viewBox="0 0 48 48" width="48" height="48">
          <circle cx="24" cy="24" r="22" fill="rgba(0,0,0,0.55)" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
          <polygon points="18,14 18,34 34,24" fill="rgba(255,255,255,0.9)"/>
        </svg>
      </button>
    </div>
    <div v-if="store.videoInfo" class="video-meta">
      <span>{{ store.activeSource?.name || '' }}</span>
      <span>{{ formatDuration(store.videoInfo.duration) }}</span>
      <span>{{ store.videoInfo.width }}x{{ store.videoInfo.height }}</span>
      <span>{{ store.videoInfo.fps.toFixed(0) }}fps</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useConfigStore } from '../stores/config.js'

const store = useConfigStore()
const videoEl = ref(null)
const paused = ref(true)
const poster = ref('')
const emit = defineEmits(['update:currentTime', 'seek'])

function onTimeUpdate() {
  if (videoEl.value) {
    emit('update:currentTime', videoEl.value.currentTime)
  }
}

function onLoaded() {
  const v = videoEl.value
  if (!v || !v.duration) return
  // Seek to 1s to capture a thumbnail for poster
  v.currentTime = Math.min(1, v.duration * 0.15)
}

function onSeeked() {
  const v = videoEl.value
  if (!v || poster.value) return
  try {
    const c = document.createElement('canvas')
    c.width = 320
    c.height = 180
    const ctx = c.getContext('2d')
    ctx.drawImage(v, 0, 0, c.width, c.height)
    poster.value = c.toDataURL('image/jpeg', 0.7)
  } catch {
    // cross-origin or other errors — skip poster
  }
}

function togglePlay() {
  const v = videoEl.value
  if (!v) return
  if (v.paused) {
    v.play().catch(() => {})
  } else {
    v.pause()
  }
}

function seek(time) {
  if (videoEl.value) {
    videoEl.value.currentTime = time
  }
}

function formatDuration(sec) {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

defineExpose({ seek })
</script>

<style scoped>
.video-preview {
  background: var(--bg-deep);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  position: relative;
}
.video-container {
  position: relative;
  background: #000;
  aspect-ratio: 16 / 9;
  max-height: 400px;
  max-width: 100%;
  margin: 0 auto;
}
.video-container video {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
}
.play-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  cursor: pointer;
  opacity: 0.85;
  transition: opacity 0.2s;
}
.play-overlay:hover {
  opacity: 1;
}
.play-overlay svg {
  filter: drop-shadow(0 2px 8px rgba(0,0,0,0.4));
}
.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 280px;
  color: var(--text-muted);
  font-size: 13px;
}
.video-meta {
  display: flex;
  gap: 16px;
  padding: 8px 14px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-surface);
  border-top: 1px solid var(--border);
}
</style>
