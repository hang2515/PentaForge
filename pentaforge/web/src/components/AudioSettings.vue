<template>
  <div class="audio-settings">
    <div class="audio-mode" role="group" aria-label="音频模式">
      <button
        type="button"
        :class="{ active: !store.audio_enabled }"
        @click="store.audio_enabled = false"
      >
        <strong>模式 1</strong>
        <span>保留原声</span>
      </button>
      <button
        type="button"
        :class="{ active: store.audio_enabled }"
        @click="store.audio_enabled = true"
      >
        <strong>模式 2</strong>
        <span>替换音频</span>
      </button>
    </div>

    <div v-if="!store.audio_enabled" class="mode-note">
      保留源视频中的原始音频，不使用 BGM 和击杀音效。
    </div>

    <div v-else class="mix-settings">
      <label>BGM 文件</label>
      <div class="file-row">
        <input :value="store.bgm" @input="store.bgm = $event.target.value" placeholder="点击浏览选择 BGM 文件" />
        <button class="btn btn-sm" @click="browseBgm">浏览</button>
      </div>

      <label>BGM 音量 <span class="val">{{ Math.round(store.bgm_volume * 100) }}%</span>
        <input type="range" min="0" max="1" step="0.05" :value="store.bgm_volume" @input="store.bgm_volume = parseFloat($event.target.value)" />
      </label>

      <label>SFX 音量 <span class="val">{{ Math.round(store.sfx_volume * 100) }}%</span>
        <input type="range" min="0" max="1" step="0.05" :value="store.sfx_volume" @input="store.sfx_volume = parseFloat($event.target.value)" />
      </label>
    </div>
  </div>
</template>

<script setup>
import { useConfigStore } from '../stores/config.js'
import * as api from '../api/client.js'

const store = useConfigStore()

async function browseBgm() {
  try {
    const result = await api.openFileDialog('选择背景音乐', [
      ['Audio files', '*.mp3 *.wav *.m4a *.aac *.ogg *.flac'],
      ['All files', '*.*'],
    ])
    if (!result.cancelled && result.path) {
      store.bgm = result.path
    }
  } catch (e) { console.error(e) }
}
</script>

<style scoped>
.audio-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.audio-mode {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}
.audio-mode button {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: flex-start;
  padding: 8px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all var(--transition);
}
.audio-mode button.active {
  background: var(--gold);
  border-color: var(--gold);
  color: #fff;
}
.audio-mode strong { font-size: 12px; }
.audio-mode span { font-size: 11px; }
.mode-note {
  padding: 8px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.4;
}
.mix-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.file-row {
  display: flex;
  gap: 4px;
}
.file-row input { flex: 1; }
.file-row .btn-sm { padding: 2px 8px; font-family: var(--font-mono); }
.val {
  font-family: var(--font-mono);
  color: var(--gold);
  font-size: 10px;
}
</style>
