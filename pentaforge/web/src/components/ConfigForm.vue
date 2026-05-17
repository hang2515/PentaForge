<template>
  <div class="config-form">
    <div class="mode-toggle">
      <button :class="{ active: mode === 'form' }" @click="mode = 'form'">表单</button>
      <button :class="{ active: mode === 'yaml' }" @click="mode = 'yaml'">YAML</button>
    </div>

    <div class="source-row">
      <label>源视频</label>
      <div class="file-input-row">
        <input :value="store.source" @input="store.source = $event.target.value" placeholder="点击浏览选择文件，或手动输入路径" />
        <button class="btn-browse" @click="browseSource">浏览</button>
      </div>
    </div>

    <div v-if="mode === 'form'" class="form-panels">
      <AudioSettings
        :bgm="store.bgm" :bgm-volume="store.bgmVolume"
        :sfx-volume="store.sfxVolume" :audio-enabled="store.audio_enabled"
        @update:bgm="store.bgm = $event"
        @update:bgm-volume="store.bgmVolume = $event"
        @update:sfx-volume="store.sfxVolume = $event"
        @update:audio-enabled="store.audio_enabled = $event"
      />
      <TransitionSettings
        :type="store.transitions.type" :duration="store.transitions.duration"
        @update:type="store.transitions.type = $event"
        @update:duration="store.transitions.duration = $event"
      />
      <ExportSettings
        :exp="store.export" :output="store.output"
        @update:exp="store.export = $event"
        @update:output="store.output = $event"
      />
      <ClipEditor :clips="store.clips" @update:clips="store.clips = $event" />
    </div>

    <div v-else class="yaml-panel">
      <textarea :value="yamlText" @input="onYamlInput" spellcheck="false" />
      <div v-if="yamlError" class="yaml-error">{{ yamlError }}</div>
    </div>

    <div class="actions">
      <button class="btn" @click="saveYaml">保存 YAML</button>
      <button class="btn" @click="loadYamlPrompt">加载 YAML</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useConfigStore } from '../stores/config.js'
import * as api from '../api/client.js'
import AudioSettings from './AudioSettings.vue'
import TransitionSettings from './TransitionSettings.vue'
import ExportSettings from './ExportSettings.vue'
import ClipEditor from './ClipEditor.vue'

const store = useConfigStore()
const mode = ref('form')
const yamlError = ref('')

const yamlText = ref(store.yamlText)

watch(() => store.yamlText, (v) => {
  yamlText.value = v
})

function onYamlInput(e) {
  yamlText.value = e.target.value
  try {
    store.loadFromYaml(yamlText.value)
    yamlError.value = ''
  } catch (err) {
    yamlError.value = err.message
  }
}

async function saveYaml() {
  const text = store.yamlText
  const blob = new Blob([text], { type: 'text/yaml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'pentaforge_config.yaml'
  a.click()
  URL.revokeObjectURL(url)
}

async function browseSource() {
  try {
    const result = await api.openFileDialog('选择源视频文件', [
      ['Video files', '*.mp4 *.avi *.mkv *.mov *.webm *.flv'],
      ['All files', '*.*'],
    ])
    if (!result.cancelled && result.path) {
      store.source = result.path
    }
  } catch (e) {
    console.error('File dialog error:', e)
  }
}

function loadYamlPrompt() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.yaml,.yml'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const text = await file.text()
    try {
      store.loadFromYaml(text)
      yamlError.value = ''
      yamlText.value = text
    } catch (err) {
      yamlError.value = err.message
    }
  }
  input.click()
}
</script>

<style scoped>
.config-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.mode-toggle {
  display: flex;
  gap: 4px;
}
.mode-toggle button {
  flex: 1;
  padding: 4px;
  background: #f5ede3;
  border: 1px solid #d4b896;
  color: #8d6e63;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.mode-toggle button.active {
  background: #e07b3c;
  color: #fff;
  border-color: #e07b3c;
}
.source-row label {
  font-size: 12px;
  color: #8d6e63;
  margin-bottom: 2px;
}
.file-input-row {
  display: flex;
  gap: 6px;
}
.file-input-row input {
  flex: 1;
  background: #fef9f4;
  border: 1px solid #d4b896;
  color: #4a3728;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 13px;
}
.btn-browse {
  padding: 6px 12px;
  background: #e07b3c;
  border: none;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
}
.btn-browse:hover { background: #c96a2e; }
.form-panels {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.yaml-panel textarea {
  width: 100%;
  min-height: 400px;
  background: #fef9f4;
  border: 1px solid #d4b896;
  color: #4a3728;
  padding: 10px;
  font-family: monospace;
  font-size: 12px;
  resize: vertical;
  box-sizing: border-box;
}
.yaml-error {
  color: #c0392b;
  font-size: 12px;
  margin-top: 4px;
}
.actions {
  display: flex;
  gap: 6px;
}
</style>
