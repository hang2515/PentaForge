<template>
  <div class="audio-settings">
    <h3>音频设置</h3>
    <div class="audio-mode" role="group" aria-label="音频模式">
      <button
        type="button"
        :class="{ active: !audioEnabled }"
        @click="$emit('update:audioEnabled', false)"
      >
        <strong>模式 1</strong>
        <span>保留原声</span>
      </button>
      <button
        type="button"
        :class="{ active: audioEnabled }"
        @click="$emit('update:audioEnabled', true)"
      >
        <strong>模式 2</strong>
        <span>替换音频</span>
      </button>
    </div>

    <div v-if="!audioEnabled" class="mode-note">
      保留源视频中的原始音频，不使用 BGM 和击杀音效。
    </div>

    <div v-else class="mix-settings">
      <label class="file-label">BGM 文件</label>
      <div class="file-input-row">
        <input :value="bgm" @input="$emit('update:bgm', $event.target.value)" placeholder="点击浏览选择 BGM 文件" />
        <button class="btn-browse" @click="browseBgm">浏览</button>
      </div>
      <label>BGM 音量 <span class="val">{{ bgmVolume }}</span>
        <input type="range" min="0" max="1" step="0.05" :value="bgmVolume" @input="$emit('update:bgmVolume', parseFloat($event.target.value))" />
      </label>
      <label>SFX 音量 <span class="val">{{ sfxVolume }}</span>
        <input type="range" min="0" max="1" step="0.05" :value="sfxVolume" @input="$emit('update:sfxVolume', parseFloat($event.target.value))" />
      </label>
    </div>
  </div>
</template>

<script setup>
import * as api from '../api/client.js'

const props = defineProps({
  bgm: String,
  bgmVolume: Number,
  sfxVolume: Number,
  audioEnabled: Boolean,
})
const emit = defineEmits(['update:bgm', 'update:bgmVolume', 'update:sfxVolume', 'update:audioEnabled'])

async function browseBgm() {
  try {
    const result = await api.openFileDialog('选择背景音乐文件', [
      ['Audio files', '*.mp3 *.wav *.m4a *.aac *.ogg *.flac'],
      ['All files', '*.*'],
    ])
    if (!result.cancelled && result.path) {
      emit('update:bgm', result.path)
    }
  } catch (e) { console.error(e) }
}
</script>

<style scoped>
h3, h4 { margin: 0 0 8px; font-size: 14px; color: #5c3d2e; }
h4 { margin-top: 10px; font-size: 12px; color: #8d6e63; }
label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: #8d6e63;
  margin-bottom: 6px;
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
  background: #f5ede3;
  border: 1px solid #d4b896;
  color: #6f5546;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.audio-mode button.active {
  background: #e07b3c;
  border-color: #e07b3c;
  color: #fff;
}
.audio-mode strong { font-size: 12px; }
.audio-mode span { font-size: 11px; }
.mode-note {
  padding: 8px;
  background: #fef9f4;
  border: 1px solid #ead2b9;
  border-radius: 4px;
  color: #8d6e63;
  font-size: 12px;
  line-height: 1.4;
}
.file-label { margin-bottom: 2px; }
.file-input-row {
  display: flex;
  gap: 4px;
  margin-bottom: 6px;
}
.file-input-row input {
  flex: 1;
  font-size: 11px;
}
input { background: #fef9f4; border: 1px solid #d4b896; color: #4a3728; padding: 4px 6px; border-radius: 3px; font-size: 12px; }
input[type="range"] { padding: 0; accent-color: #e07b3c; }
.val { color: #d4742b; margin-left: 4px; }
.btn-browse {
  padding: 4px 10px;
  background: #e07b3c;
  border: none;
  color: #fff;
  border-radius: 3px;
  cursor: pointer;
  font-size: 11px;
  white-space: nowrap;
}
.btn-browse:hover { background: #c96a2e; }
</style>
