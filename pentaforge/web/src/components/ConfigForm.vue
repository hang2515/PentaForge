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

    <div class="actions">
      <button class="btn" @click="saveYaml">保存配置</button>
      <button class="btn" @click="loadYamlPrompt">加载配置</button>
    </div>
  </div>
</template>

<script setup>
import { useConfigStore } from '../stores/config.js'
import AudioSettings from './AudioSettings.vue'
import TransitionSettings from './TransitionSettings.vue'
import ExportSettings from './ExportSettings.vue'

const store = useConfigStore()

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
    } catch (err) {
      console.error('YAML load error:', err)
    }
  }
  input.click()
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

.actions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}
.actions .btn {
  flex: 1;
  text-align: center;
}
</style>
