<template>
  <div class="video-panel">
    <div class="section-title">视频素材</div>
    <div class="source-cards">
      <div
        v-for="(src, i) in store.sources"
        :key="i"
        class="source-card"
        :class="{ active: i === store.activeSourceIndex }"
        @click="store.setActiveSource(i)"
      >
        <div class="card-thumb">
          <svg viewBox="0 0 64 36" width="64" height="36">
            <rect width="64" height="36" rx="3" fill="var(--bg-deep)" stroke="var(--border)" stroke-width="0.5"/>
            <polygon points="26,11 26,25 38,18" fill="var(--gold-dim)"/>
          </svg>
        </div>
        <div class="card-info">
          <div class="card-name" :title="src.name">{{ src.name }}</div>
          <div class="card-meta" v-if="src.info">{{ formatDuration(src.info.duration) }}</div>
          <div class="card-meta" v-else>---</div>
        </div>
        <button
          v-if="store.sources.length > 1"
          class="btn-icon card-remove"
          @click.stop="store.removeSource(i)"
          title="移除"
        >&times;</button>
      </div>
    </div>
    <button class="btn btn-primary add-source-btn" @click="browseSource">+ 添加视频</button>
  </div>
</template>

<script setup>
import { useConfigStore } from '../stores/config.js'
import * as api from '../api/client.js'

const store = useConfigStore()

async function browseSource() {
  try {
    const result = await api.openFileDialog('选择视频文件', [
      ['Video files', '*.mp4 *.avi *.mkv *.mov *.webm *.flv'],
      ['All files', '*.*'],
    ])
    if (!result.cancelled) {
      const paths = result.paths?.length ? result.paths : result.path ? [result.path] : []
      for (const path of paths) {
        store.addSource(path)
        try {
          const info = await api.getVideoInfo(path)
          store.setSourceInfo(path, info)
        } catch (e) {
          console.error('Failed to load video info:', e)
        }
      }
    }
  } catch (e) {
    console.error('File dialog error:', e)
  }
}

function formatDuration(sec) {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}
</script>

<style scoped>
.video-panel {
  padding: 14px 14px 10px;
  border-bottom: 1px solid var(--border);
}

.source-cards {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
  max-height: 200px;
  overflow-y: auto;
}

.source-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition);
  position: relative;
}
.source-card:hover {
  border-color: var(--border-accent);
}
.source-card.active {
  border-color: var(--gold-dim);
  box-shadow: 0 0 12px var(--gold-glow);
}

.card-thumb {
  flex-shrink: 0;
  border-radius: 3px;
  overflow: hidden;
  line-height: 0;
}

.card-info {
  flex: 1;
  min-width: 0;
}
.card-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-meta {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
}

.card-remove {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity var(--transition);
}
.source-card:hover .card-remove { opacity: 1; }

.add-source-btn {
  width: 100%;
  text-align: center;
}
</style>
