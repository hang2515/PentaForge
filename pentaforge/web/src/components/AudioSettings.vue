<template>
  <div class="audio-settings">
    <label class="switch-row">
      <span>启用音频混音</span>
      <input type="checkbox" :checked="store.audio_enabled" @change="store.audio_enabled = $event.target.checked" />
    </label>

    <label>BGM 文件</label>
    <div class="file-row">
      <input :value="store.bgm" @input="store.bgm = $event.target.value" placeholder="选择背景音乐..." />
      <button class="btn btn-sm" @click="browseBgm">...</button>
    </div>

    <label>BGM 音量 <span class="val">{{ Math.round(store.bgm_volume * 100) }}%</span>
      <input type="range" min="0" max="1" step="0.05" :value="store.bgm_volume" @input="store.bgm_volume = parseFloat($event.target.value)" />
    </label>

    <label>SFX 音量 <span class="val">{{ Math.round(store.sfx_volume * 100) }}%</span>
      <input type="range" min="0" max="1" step="0.05" :value="store.sfx_volume" @input="store.sfx_volume = parseFloat($event.target.value)" />
    </label>
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
.switch-row {
  flex-direction: row !important;
  align-items: center;
  justify-content: space-between;
  color: var(--text-primary) !important;
  font-size: 12px !important;
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
