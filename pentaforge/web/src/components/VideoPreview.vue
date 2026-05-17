<template>
  <div class="video-preview">
    <div v-if="!store.source" class="placeholder">
      <p>请选择源视频文件</p>
    </div>
    <video
      v-else
      ref="videoEl"
      :src="store.videoSrc"
      controls
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoaded"
    />
    <div v-if="store.videoInfo" class="video-meta">
      {{ formatDuration(store.videoInfo.duration) }} | {{ store.videoInfo.width }}x{{ store.videoInfo.height }} | {{ store.videoInfo.fps.toFixed(2) }} fps
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useConfigStore } from '../stores/config.js'
import * as api from '../api/client.js'

const store = useConfigStore()
const videoEl = ref(null)
const emit = defineEmits(['update:currentTime', 'seek'])

function onTimeUpdate() {
  if (videoEl.value) {
    emit('update:currentTime', videoEl.value.currentTime)
  }
}

function onLoaded() {
}

watch(() => store.source, async (path) => {
  if (!path) {
    store.videoInfo = null
    return
  }
  try {
    store.videoInfo = await api.getVideoInfo(path)
  } catch (e) {
    console.error('Failed to load video info:', e)
    store.videoInfo = null
  }
})

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
  background: #f5ede3;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 8px;
  border: 1px solid #e8d5c4;
}
.video-preview video {
  width: 100%;
  display: block;
  max-height: 360px;
}
.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 240px;
  color: #b8a088;
}
.video-meta {
  padding: 6px 12px;
  color: #8d6e63;
  font-size: 12px;
  background: #fef9f4;
}
</style>
