<template>
  <div class="export-settings">
    <div class="row">
      <label>分辨率
        <input :value="store.export.resolution" @input="set('resolution', $event.target.value)" placeholder="1920x1080" />
      </label>
      <label>帧率
        <input type="number" :value="store.export.fps" @input="set('fps', parseInt($event.target.value) || 60)" />
      </label>
    </div>
    <div class="row">
      <label>编码器
        <select :value="store.export.codec" @change="set('codec', $event.target.value)">
          <option value="libx264">H.264</option>
          <option value="libx265">H.265</option>
        </select>
      </label>
      <label>码率
        <input :value="store.export.bitrate" @input="set('bitrate', $event.target.value)" placeholder="12M" />
      </label>
    </div>
    <label>编码预设
      <select :value="store.export.preset" @change="set('preset', $event.target.value)">
        <option value="ultrafast">ultrafast</option>
        <option value="veryfast">veryfast</option>
        <option value="fast">fast</option>
        <option value="medium">medium</option>
        <option value="slow">slow</option>
      </select>
    </label>
    <label>输出文件
      <div class="output-row">
        <input :value="store.output" @input="store.output = $event.target.value" placeholder="highlight_output.mp4" />
        <button class="btn" @click="browseOutput">浏览</button>
      </div>
    </label>
  </div>
</template>

<script setup>
import { useConfigStore } from '../stores/config.js'
import { saveFileDialog } from '../api/client.js'

const store = useConfigStore()

function set(key, val) {
  store.export = { ...store.export, [key]: val }
}

async function browseOutput() {
  const { path, cancelled } = await saveFileDialog('选择导出位置', store.output || 'highlight_output.mp4')
  if (!cancelled && path) {
    store.output = path
  }
}
</script>

<style scoped>
.export-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.row { display: flex; gap: 8px; }
.row label { flex: 1; }
.output-row {
  display: flex;
  gap: 6px;
}
.output-row input {
  flex: 1;
}
.output-row .btn {
  flex-shrink: 0;
  padding: 6px 14px;
}
</style>
