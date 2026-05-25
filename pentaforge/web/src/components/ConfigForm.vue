<template>
  <div class="config-form">
    <details class="settings-section" open>
      <summary class="section-title">
        <svg width="12" height="12" viewBox="0 0 12 12"><path d="M6 1L6 11M1 6L11 6" stroke="currentColor" stroke-width="1.5"/></svg>
        音频设置
      </summary>
      <AudioSettings />
    </details>

    <details class="settings-section">
      <summary class="section-title">
        <svg width="12" height="12" viewBox="0 0 12 12"><path d="M6 1L6 11M1 6L11 6" stroke="currentColor" stroke-width="1.5"/></svg>
        转场设置
      </summary>
      <TransitionSettings />
    </details>

    <details class="settings-section">
      <summary class="section-title">
        <svg width="12" height="12" viewBox="0 0 12 12"><path d="M6 1L6 11M1 6L11 6" stroke="currentColor" stroke-width="1.5"/></svg>
        导出设置
      </summary>
      <ExportSettings />
    </details>

    <div class="config-save">
      <label>配置文件名
        <div class="save-row">
          <input v-model="filename" placeholder="pentaforge_config.yaml" />
          <button class="btn" @click="saveYaml">保存</button>
        </div>
      </label>
    </div>
    <div class="actions">
      <button class="btn" @click="loadYamlPrompt">加载配置</button>
    </div>
    <div v-if="status" class="status" :class="{ error: status.includes('失败') }">{{ status }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useConfigStore } from '../stores/config.js'
import * as api from '../api/client.js'
import AudioSettings from './AudioSettings.vue'
import TransitionSettings from './TransitionSettings.vue'
import ExportSettings from './ExportSettings.vue'

const store = useConfigStore()
const status = ref('')
const filename = ref('')

const YAML_FILETYPES = [['YAML files', '*.yaml *.yml'], ['All files', '*.*']]

// Update default filename when source changes
import { watch } from 'vue'
watch(() => store.activeSource?.name, (name) => {
  if (name && !filename.value) {
    filename.value = name.replace(/\.[^\\/]+$/, '.yaml')
  }
}, { immediate: true })

async function getConfigDir() {
  try {
    const ws = await api.getWorkspace()
    return ws.yaml_dir
  } catch {
    return ''
  }
}

async function saveYaml() {
  status.value = ''
  const configDir = await getConfigDir()
  const name = filename.value || 'pentaforge_config.yaml'
  if (!name.endsWith('.yaml') && !name.endsWith('.yml')) {
    filename.value = name + '.yaml'
  }
  const outputPath = configDir ? `${configDir}/${filename.value}` : filename.value

  try {
    const result = await api.saveConfigYaml(store.yamlText, outputPath)
    status.value = `已保存: ${result.saved_path}`
  } catch (err) {
    status.value = `保存失败: ${err.message}`
  }
}

async function loadYamlPrompt() {
  status.value = ''
  const configDir = await getConfigDir()

  try {
    const result = await api.openFileDialog('选择配置文件', YAML_FILETYPES, configDir)
    if (result.cancelled) return
    const paths = result.paths?.length ? result.paths : result.path ? [result.path] : []
    if (!paths.length) return
    const loadResult = await api.loadConfig(paths[0])
    store.loadFromYaml(loadResult.yaml_text)
    // Update filename to the loaded file's name
    const loadedName = paths[0].split(/[/\\]/).pop()
    if (loadedName) filename.value = loadedName
    status.value = '配置已加载'
  } catch (err) {
    status.value = `加载失败: ${err.message}`
  }
}
</script>

<style scoped>
.config-form {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.settings-section {
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color var(--transition);
}
.settings-section:hover {
  border-color: var(--border-accent);
}
.settings-section[open] {
  border-color: var(--border-accent);
}

.settings-section summary {
  padding: 10px 14px;
  cursor: pointer;
  list-style: none;
  display: flex;
  align-items: center;
  gap: 8px;
  user-select: none;
  transition: color var(--transition);
}
.settings-section summary::-webkit-details-marker { display: none; }
.settings-section summary:hover {
  color: var(--gold-light);
}
.settings-section summary svg {
  transition: transform 0.2s;
  flex-shrink: 0;
}
.settings-section[open] summary svg {
  transform: rotate(45deg);
}

.settings-section > :not(summary) {
  padding: 0 14px 12px;
}

.config-save {
  margin-top: 8px;
}
.save-row {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}
.save-row input {
  flex: 1;
  min-width: 0;
}
.save-row .btn {
  flex-shrink: 0;
}
.actions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}
.actions .btn {
  flex: 1;
  text-align: center;
}
.status {
  margin-top: 6px;
  font-size: 11px;
  color: var(--accent-green);
  word-break: break-all;
}
.status.error {
  color: var(--accent-red);
}
</style>
