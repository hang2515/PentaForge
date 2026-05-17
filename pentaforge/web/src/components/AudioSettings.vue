<template>
  <div class="audio-settings">
    <h3>音频设置</h3>
    <label class="switch-row">
      <span>启用音频混音</span>
      <input type="checkbox" :checked="audioEnabled" @change="$emit('update:audioEnabled', $event.target.checked)" />
    </label>
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
.switch-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #5c3d2e;
  margin-bottom: 8px;
}
.switch-row input[type="checkbox"] { width: 16px; height: 16px; accent-color: #e07b3c; }
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
